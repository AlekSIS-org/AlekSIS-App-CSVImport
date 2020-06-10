from typing import Union
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
    has_is_active_field,
    is_active,
)
from aleksis.core.models import Group, Person
from aleksis.core.util.core_helpers import (
    DummyRecorder,
    celery_optional_progress,
    get_site_preferences,
)


@celery_optional_progress
def import_csv(
    recorder: Union["ProgressRecorder", DummyRecorder], template: int, filename: str,
) -> None:
    csv = open(filename, "rb")

    template = ImportTemplate.objects.get(pk=template)
    model = template.content_type.model_class()

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
                if FieldType.UNIQUE_REFERENCE.value in row:
                    instance, created = model.objects.update_or_create(
                        import_ref_csv=row[FieldType.UNIQUE_REFERENCE.value],
                        defaults=update_dict,
                    )
                elif FieldType.SHORT_NAME.value in row:
                    instance, created = model.objects.update_or_create(
                        short_name=row[FieldType.SHORT_NAME.value], defaults=update_dict
                    )
                else:
                    raise ValueError(_("Missing import reference or short name."))
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
