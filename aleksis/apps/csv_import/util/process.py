from typing import Optional, Union
from uuid import uuid4

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

import pandas
from pandas.errors import ParserError

from aleksis.apps.csv_import.models import (
    ALLOWED_FIELD_TYPES_FOR_MODELS,
    DATA_TYPES,
    FIELD_MAPPINGS,
    FIELD_TYPES_MULTIPLE,
    FieldType,
    ImportTemplate,
)
from aleksis.apps.csv_import.settings import FALSE_VALUES, TRUE_VALUES
from aleksis.apps.csv_import.util.converters import CONVERTERS
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
        # Get column header
        if field.field_type_enum == FieldType.IGNORE:
            # Create random header for ignoring (leading _)
            key = f"_ignore_{uuid4()}"
        elif field.field_type_enum in FIELD_TYPES_MULTIPLE:
            key = f"{field.field_type}_{uuid4()}"
            cols_for_multiple_fields.setdefault(field.field_type_enum, [])
            cols_for_multiple_fields[field.field_type_enum].append(key)
        else:
            # Use key of enum for other data types
            key = field.field_type

        # Get data type
        if field.field_type in DATA_TYPES:
            data_type = DATA_TYPES[field.field_type]

            data_types[key] = data_type

        cols.append(key)
    try:
        data = pandas.read_csv(
            csv,
            sep=template.separator,
            names=cols,
            header=0 if template.has_header_row else None,
            dtype=data_types,
            usecols=lambda k: not k.startswith("_"),
            keep_default_na=False,
            converters=CONVERTERS,
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
    if FieldType.PEDASOS_CLASS_RANGE.value in cols:
        classes_per_short_name = get_classes_per_short_name()
        classes_per_grade = get_classes_per_grade(classes_per_short_name.keys())

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
            if key in FieldType.value_dict:
                enum_key = FieldType.value_dict[key]
                if enum_key in FIELD_MAPPINGS:
                    update_dict[FIELD_MAPPINGS[enum_key]] = value

        # Set name to short name if there is no name field
        if (
            FieldType.NAME in ALLOWED_FIELD_TYPES_FOR_MODELS[model]
            and FieldType.NAME.value not in row
            and FieldType.SHORT_NAME.value in row
        ):
            update_dict[FIELD_MAPPINGS[FieldType.NAME]] = row[
                FieldType.SHORT_NAME.value
            ]

        # Set short name to name if there is no short name field
        if (
            FieldType.SHORT_NAME in ALLOWED_FIELD_TYPES_FOR_MODELS[model]
            and FieldType.SHORT_NAME.value not in row
            and FieldType.NAME.value in row
        ):
            update_dict[FIELD_MAPPINGS[FieldType.SHORT_NAME]] = row[
                FieldType.NAME.value
            ]

        if template.group_type and model == Group:
            update_dict["group_type"] = template.group_type

        if obj_is_active:
            created = False

            try:
                get_dict = {"defaults": update_dict}
                if FieldType.UNIQUE_REFERENCE.value in row:
                    get_dict["import_ref_csv"] = row[FieldType.UNIQUE_REFERENCE.value]
                elif FieldType.SHORT_NAME.value in row:
                    get_dict["short_name"] = row[FieldType.SHORT_NAME.value]
                else:
                    raise ValueError(_("Missing import reference or short name."))

                if model == Group and school_term:
                    get_dict["school_term"] = school_term

                instance, created = model.objects.update_or_create(**get_dict)
            except (ValueError, ValidationError) as e:
                recorder.add_message(
                    messages.ERROR,
                    _(f"Failed to import {model._meta.verbose_name} {row}:\n{e}"),
                    fail_silently=True,
                )
                all_ok = False

            # Get values for multiple fields
            values_for_multiple_fields = {}
            for field_type, cols_for_field_type in cols_for_multiple_fields.items():
                values_for_multiple_fields[field_type] = []
                for col in cols_for_field_type:
                    value = row[col]
                    values_for_multiple_fields[field_type].append(value)

            # Create department groups
            if (
                FieldType.DEPARTMENTS.value in row
                and get_site_preferences()["csv_import__group_type_departments"]
            ):
                subjects = row[FieldType.DEPARTMENTS.value]

                departments = create_department_groups(subjects)

                # Set current person as member of this department
                instance.member_of.add(*departments)

            # Group owners
            if FieldType.GROUP_OWNER_BY_SHORT_NAME in values_for_multiple_fields:
                short_names = values_for_multiple_fields[
                    FieldType.GROUP_OWNER_BY_SHORT_NAME
                ]
                group_owners = bulk_get_or_create(
                    Person,
                    short_names,
                    attr="short_name",
                    default_attrs="last_name",
                    defaults={"first_name": "?"},
                )
                instance.owners.set(group_owners)

            # Group subject
            if FieldType.SUBJECT_BY_SHORT_NAME.value in row:
                subject = get_subject_by_short_name(
                    row[FieldType.SUBJECT_BY_SHORT_NAME.value]
                )
                instance.subject = subject
                instance.save()

            # Class range
            if FieldType.PEDASOS_CLASS_RANGE.value in row:
                classes = parse_class_range(
                    classes_per_short_name,
                    classes_per_grade,
                    row[FieldType.PEDASOS_CLASS_RANGE.value],
                )
                instance.parent_groups.set(classes)

            # Group memberships
            if FieldType.GROUP_BY_SHORT_NAME in values_for_multiple_fields:
                short_names = values_for_multiple_fields[FieldType.GROUP_BY_SHORT_NAME]
                groups = Group.objects.filter(short_name__in=short_names)
                instance.member_of.add(*groups)

            # Guardians
            if (
                FieldType.GUARDIAN_FIRST_NAME in values_for_multiple_fields
                and FieldType.GUARDIAN_LAST_NAME in values_for_multiple_fields
            ):
                first_names = values_for_multiple_fields[FieldType.GUARDIAN_FIRST_NAME]
                last_names = values_for_multiple_fields[FieldType.GUARDIAN_LAST_NAME]

                if len(first_names) != len(last_names):
                    recorder.add_message(
                        messages.ERROR,
                        _(
                            "Failed to import guardians: Each guardian needs a first and a last name."
                        ),
                    )

                emails = []
                if FieldType.GUARDIAN_EMAIL in values_for_multiple_fields:
                    emails = values_for_multiple_fields[FieldType.GUARDIAN_EMAIL]

                guardians = create_guardians(first_names, last_names, emails)
                instance.guardians.set(guardians)

                guardian_group = get_site_preferences()["csv_import__group_guardians"]
                if guardian_group:
                    guardian_group.members.add(*guardians)

            if template.group and isinstance(instance, Person):
                instance.member_of.add(template.group)

            if created:
                created_count += 1

            recorder.set_progress(i + 1)
        else:
            # Store import refs to deactivate later
            inactive_refs.append(row[FieldType.UNIQUE_REFERENCE.value])

    # Deactivate all persons that existed but are now inactive
    if inactive_refs and has_is_active_field(model):
        affected = model.objects.filter(
            import_ref_csv__in=inactive_refs, is_active=True
        ).update(is_active=False)

        if affected:
            recorder.add_message(
                messages.WARNING,
                _(
                    f"{affected} existing {model._meta.verbose_name_plural} were deactivated."
                ),
            )

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
