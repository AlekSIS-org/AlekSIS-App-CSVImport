from typing import Optional, Union

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

import pandas
from pandas.errors import ParserError

from aleksis.apps.csv_import.field_types import (
    MultipleValuesFieldType,
    field_type_registry,
    DirectMappingFieldType,
)
from aleksis.apps.csv_import.models import ImportTemplate
from aleksis.apps.csv_import.settings import FALSE_VALUES, TRUE_VALUES
from aleksis.apps.csv_import.util.import_helpers import (
    bulk_get_or_create,
    create_department_groups,
    create_guardians,
    get_subject_by_short_name,
    has_is_active_field,
    is_active,
)
from aleksis.apps.csv_import.util.pedasos_helpers import (
    get_classes_per_grade,
    get_classes_per_short_name,
    parse_class_range,
)
from aleksis.core.models import Group, Person, SchoolTerm
from aleksis.core.util.core_helpers import (
    DummyRecorder,
    celery_optional_progress,
    get_site_preferences,
)


@celery_optional_progress
def import_csv(
    recorder: Union["ProgressRecorder", DummyRecorder],
    template: int,
    filename: str,
    school_term: Optional[int] = None,
) -> None:
    csv = open(filename, "rb")

    template = ImportTemplate.objects.get(pk=template)
    model = template.content_type.model_class()

    if school_term:
        school_term = SchoolTerm.objects.get(pk=school_term)

    data_types = {}
    cols = []
    cols_for_multiple_fields = {}
    for field in template.fields.all():
        field_type = field.field_type_class
        column_name = field_type.column_name

        # Get column header
        if issubclass(field_type, MultipleValuesFieldType):
            cols_for_multiple_fields.setdefault(field_type, [])
            cols_for_multiple_fields[field_type].append(column_name)

        # Get data type
        data_types[column_name] = field_type.data_type

        cols.append(column_name)
        print(cols)
    try:
        data = pandas.read_csv(
            csv,
            sep=template.separator,
            names=cols,
            header=0 if template.has_header_row else None,
            dtype=data_types,
            usecols=lambda k: not k.startswith("_"),
            keep_default_na=False,
            converters=field_type_registry.converters,
            quotechar='"',
            encoding="utf-8-sig",
            true_values=TRUE_VALUES,
            false_values=FALSE_VALUES,
        )
    except ParserError as e:
        recorder.add_message(
            messages.ERROR, _(f"There was an error while parsing the CSV file:\n{e}")
        )
        return

    # Exclude all empty rows
    data = data.where(data.notnull(), None)

    # Preload some data
    # if FieldType.PEDASOS_CLASS_RANGE.value in cols:
    #     classes_per_short_name = get_classes_per_short_name(school_term)
    #     classes_per_grade = get_classes_per_grade(classes_per_short_name.keys())

    all_ok = True
    inactive_refs = []
    created_count = 0

    data_as_dict = data.transpose().to_dict().values()
    recorder.total = len(data_as_dict)

    for i, row in enumerate(data_as_dict):
        # Fill the is_active field from other fields if necessary
        obj_is_active = is_active(row)
        if has_is_active_field(model):
            row["is_active"] = obj_is_active

        # Build dict with all fields that should be directly updated
        update_dict = {}
        for key, value in row.items():
            if key in field_type_registry.field_types:
                field_type = field_type_registry.get_from_name(key)
                if issubclass(field_type, DirectMappingFieldType):
                    update_dict[field_type.db_field] = value

        # Set alternatives for some fields
        for (
            field_type_origin,
            alternative_name,
        ) in field_type_registry.alternatives.items():
            if (
                model in field_type_origin.models
                and field_type_origin.name not in row
                and alternative_name in row
            ):
                update_dict[field_type_origin.name] = row[alternative_name]

        if template.group_type and model == Group:
            update_dict["group_type"] = template.group_type

        if obj_is_active:
            created = False

            try:
                get_dict = {"defaults": update_dict}

                match_field_found = False
                for (
                    priority,
                    match_field_type,
                ) in field_type_registry.match_field_types:
                    if match_field_type.name in row:
                        get_dict[match_field_type.db_field] = row[
                            match_field_type.name
                        ]
                        match_field_found = True
                        break

                if not match_field_found:
                    raise ValueError(_("Missing unique reference."))

                if hasattr(model, "school_term") and school_term:
                    get_dict["school_term"] = school_term

                print(get_dict)

                instance, created = model.objects.update_or_create(**get_dict)

                # Get values for multiple fields
                values_for_multiple_fields = {}
                for field_type, cols_for_field_type in cols_for_multiple_fields.items():
                    values_for_multiple_fields[field_type] = []
                    for col in cols_for_field_type:
                        value = row[col]
                        values_for_multiple_fields[field_type].append(value)

                # Create department groups
                # if (
                #     FieldType.DEPARTMENTS.value in row
                #     and get_site_preferences()["csv_import__group_type_departments"]
                # ):
                #     subjects = row[FieldType.DEPARTMENTS.value]
                #
                #     departments = create_department_groups(subjects)
                #
                # Set current person as member of this department
                # instance.member_of.add(*departments)

                # Group owners
                # if FieldType.GROUP_OWNER_BY_SHORT_NAME in values_for_multiple_fields:
                #     short_names = values_for_multiple_fields[
                #         FieldType.GROUP_OWNER_BY_SHORT_NAME
                #     ]
                #     group_owners = bulk_get_or_create(
                #         Person,
                #         short_names,
                #         attr="short_name",
                #         default_attrs="last_name",
                #         defaults={"first_name": "?"},
                #     )
                #     instance.owners.set(group_owners)
                #
                # Group subject
                # if FieldType.SUBJECT_BY_SHORT_NAME.value in row:
                #     subject = get_subject_by_short_name(
                #         row[FieldType.SUBJECT_BY_SHORT_NAME.value]
                #     )
                #     instance.subject = subject
                #     instance.save()
                #
                # Class range
                # if FieldType.PEDASOS_CLASS_RANGE.value in row:
                #     classes = parse_class_range(
                #         classes_per_short_name,
                #         classes_per_grade,
                #         row[FieldType.PEDASOS_CLASS_RANGE.value],
                #     )
                #     instance.parent_groups.set(classes)

                # Primary group
                # if FieldType.PRIMARY_GROUP_BY_SHORT_NAME.value in row:
                #     short_name = row[FieldType.PRIMARY_GROUP_BY_SHORT_NAME.value]
                #     try:
                #         group = Group.objects.get(
                #             short_name=short_name, school_term=school_term
                #         )
                #         instance.primary_group = group
                #         instance.member_of.add(group)
                #         instance.save()
                #     except Group.DoesNotExist:
                #         recorder.add_message(
                #             messages.ERROR,
                #             _(
                #                 f"{instance}: Failed to import the primary group: "
                #                 f"Group {short_name} does not exist in school term {school_term}."
                #             ),
                #         )

                # Group memberships
                # if FieldType.GROUP_BY_SHORT_NAME in values_for_multiple_fields:
                #     short_names = values_for_multiple_fields[FieldType.GROUP_BY_SHORT_NAME]
                #     groups = Group.objects.filter(
                #         short_name__in=short_names, school_term=school_term
                #     )
                #     instance.member_of.add(*groups)

                # Guardians
                # if (
                #     FieldType.GUARDIAN_FIRST_NAME in values_for_multiple_fields
                #     and FieldType.GUARDIAN_LAST_NAME in values_for_multiple_fields
                # ):
                #     first_names = values_for_multiple_fields[FieldType.GUARDIAN_FIRST_NAME]
                #     last_names = values_for_multiple_fields[FieldType.GUARDIAN_LAST_NAME]
                #
                #     if len(first_names) != len(last_names):
                #         recorder.add_message(
                #             messages.ERROR,
                #             _(
                #                 "Failed to import guardians: Each guardian needs a first and a last name."
                #             ),
                #         )
                #
                #     emails = []
                #     if FieldType.GUARDIAN_EMAIL in values_for_multiple_fields:
                #         emails = values_for_multiple_fields[FieldType.GUARDIAN_EMAIL]
                #
                #     guardians = create_guardians(first_names, last_names, emails)
                #     instance.guardians.set(guardians)
                #
                #     guardian_group = get_site_preferences()["csv_import__group_guardians"]
                #     if guardian_group:
                #         guardian_group.members.add(*guardians)

                if template.group and isinstance(instance, Person):
                    instance.member_of.add(template.group)

                if created:
                    created_count += 1

            except (ValueError, ValidationError) as e:
                recorder.add_message(
                    messages.ERROR,
                    _(f"Failed to import {model._meta.verbose_name} {row}:\n{e}"),
                    fail_silently=True,
                )
                all_ok = False

            recorder.set_progress(i + 1)
        else:
            # Store import refs to deactivate later
            inactive_refs.append(
                row[field_type_registry.match_field_types[0][1].name]
            )  # WONT WORK AS WANTED

        # Deactivate all persons that existed but are now inactive
        # unique_field = field_type_registry.unique_references[0][1]
        args = {f"__in"}
        # affected = model.objects.filter(
        #     import_ref_csv__in=inactive_refs, is_active=True
        # ).update(is_active=False)
        #
        # if affected:
        #     recorder.add_message(
        #         messages.WARNING,
        #         _(
        #             f"{affected} existing {model._meta.verbose_name_plural} were deactivated."
        #         ),
        #     )

    if created_count:
        recorder.add_message(
            messages.SUCCESS,
            _(f"{created_count} {model._meta.verbose_name_plural} were newly created."),
        )

    if all_ok:
        recorder.add_message(
            messages.SUCCESS,
            _(f"All {model._meta.verbose_name_plural} were imported successfully."),
        )
    else:
        recorder.add_message(
            messages.WARNING,
            _(f"Some {model._meta.verbose_name_plural} failed to be imported."),
        )
