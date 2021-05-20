from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

import pandas
from pandas.errors import ParserError

from aleksis.apps.csv_import.field_types import (
    DirectMappingFieldType,
    MultipleValuesFieldType,
    field_type_registry,
)
from aleksis.apps.csv_import.settings import FALSE_VALUES, TRUE_VALUES
from aleksis.apps.csv_import.util.import_helpers import has_is_active_field, is_active
from aleksis.core.models import Group, Person
from aleksis.core.util.celery_progress import ProgressRecorder, recorded_task

from ..models import ImportJob


@recorded_task
def import_csv(import_job: int, recorder: ProgressRecorder,) -> None:
    import_job = ImportJob.objects.get(pk=import_job)
    template = import_job.template
    model = template.content_type.model_class()
    school_term = import_job.school_term
    csv = import_job.data_file.open("rb")

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

        # Prepare field type for import
        field_type.prepare(school_term)

        cols.append(column_name)
        print(cols)
    try:
        data = pandas.read_csv(
            csv,
            sep=template.parsed_separator,
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

    all_ok = True
    inactive_refs = []
    created_count = 0

    data_as_dict = data.transpose().to_dict().values()

    for row in recorder.iterate(data_as_dict):
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
        for (field_type_origin, alternative_name,) in field_type_registry.alternatives.items():
            if (
                model in field_type_origin.models
                and field_type_origin.name not in row
                and alternative_name in row
            ):
                update_dict[field_type_origin.name] = row[alternative_name]

        if template.group_type and model == Group:
            update_dict["group_type"] = template.group_type

        get_dict = {}
        match_field_found = False
        for (priority, match_field_type,) in field_type_registry.match_field_types:
            if match_field_type.name in row:
                get_dict[match_field_type.db_field] = row[match_field_type.name]
                match_field_found = True
                break

        if not match_field_found:
            raise ValueError(_("Missing unique reference."))

        if hasattr(model, "school_term") and school_term:
            get_dict["school_term"] = school_term

        if obj_is_active:
            created = False

            try:
                get_dict["defaults"] = update_dict

                instance, created = model.objects.update_or_create(**get_dict)

                # Get values for multiple fields
                values_for_multiple_fields = {}
                for field_type, cols_for_field_type in cols_for_multiple_fields.items():
                    values_for_multiple_fields[field_type] = []
                    for col in cols_for_field_type:
                        value = row[col]
                        values_for_multiple_fields[field_type].append(value)

                    # Process
                    field_type().process(instance, values_for_multiple_fields[field_type])

                # Process field types with custom logic
                for process_field_type in field_type_registry.process_field_types:
                    if process_field_type.name in row:
                        try:
                            process_field_type().process(instance, row[process_field_type.name])
                        except RuntimeError as e:
                            recorder.add_message(messages.ERROR, str(e))

                if template.group and isinstance(instance, Person):
                    instance.member_of.add(template.group)

                if created:
                    created_count += 1

            except (
                ValueError,
                ValidationError,
                model.MultipleObjectsReturned,
                model.DoesNotExist,
            ) as e:
                recorder.add_message(
                    messages.ERROR, _(f"Failed to import {model._meta.verbose_name} {row}:\n{e}"),
                )
                all_ok = False

        else:
            # Store import refs to deactivate later
            try:
                obj = model.objects.get(**get_dict)
                inactive_refs.append(obj.pk)
            except model.DoesNotExist:
                pass

        # Deactivate all persons that existed but are now inactive
        affected = None
        if has_is_active_field(model):
            affected = model.objects.filter(pk__in=inactive_refs, is_active=True).update(
                is_active=False
            )

        if affected:
            recorder.add_message(
                messages.WARNING,
                _(f"{affected} existing {model._meta.verbose_name_plural} were deactivated."),
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
            messages.WARNING, _(f"Some {model._meta.verbose_name_plural} failed to be imported."),
        )
