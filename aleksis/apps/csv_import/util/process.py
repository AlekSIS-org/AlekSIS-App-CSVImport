from datetime import datetime, date
from typing import BinaryIO, Optional, Union
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.http import HttpRequest
from django.utils.translation import gettext as _

import pandas
import phonenumbers
from pandas.errors import ParserError

from aleksis.apps.csv_import.models import (
    ImportTemplate,
    FieldType,
    DATA_TYPES,
    FIELD_MAPPINGS,
)
from aleksis.core.util import messages

STATE_ACTIVE = (True, 2)
TRUE_VALUES = ["+", "Ja"]
FALSE_VALUES = ["-", "Nein"]
DATE_FIELDS = ["date_of_birth"]
PHONE_NUMBER_COUNTRY = "DE"
SEXES = {
    "w": "f",
    "m": "m",
    "weiblich": "f",
    "männlich": "m",
}


def is_active(row: dict) -> bool:
    """Find out whether an imported object is active."""

    if "is_active" in row:
        return row["is_active"] in STATE_ACTIVE

    return True


def parse_phone_number(value: Optional[str]):
    if value:
        return phonenumbers.parse(value, PHONE_NUMBER_COUNTRY)
    else:
        ""


def parse_sex(value: Optional[str]):
    if value:
        value = value.lower()
        if value in SEXES:
            return SEXES[value]

    return ""


def parse_dd_mm_yyyy(value: Optional[str]) -> Optional[date]:
    """Parse string date (format: DD.MM.YYYY)."""
    if value:
        return datetime.strptime(value, "%d.%m.%Y").date()
    return None


CSV_CONVERTERS = {
    FieldType.PHONE_NUMBER.value: parse_phone_number,
    FieldType.MOBILE_NUMBER.value: parse_phone_number,
    FieldType.SEX.value: parse_sex,
    FieldType.SUBJECTS.value: lambda val: val.split(","),
    FieldType.DATE_OF_BIRTH_DD_MM_YYYY.value: parse_dd_mm_yyyy,
}


def import_csv(
    request: Union[HttpRequest, None],
    template: ImportTemplate,
    csv: Union[BinaryIO, str],
) -> None:
    model = template.content_type.model_class()

    data_types = {}
    cols = []
    for field in template.fields.all():
        # Get column header
        if field.field_type_enum == FieldType.IGNORE:
            # Create random header for ignoring (leading _)
            key = f"_ignore_{uuid4()}"
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
            converters=CSV_CONVERTERS,
            quotechar='"',
            encoding="utf-8-sig",
            true_values=TRUE_VALUES,
            false_values=FALSE_VALUES,
        )
    except ParserError as e:
        messages.error(request, _(f"There was an error while parsing the CSV file:\n{e}"))
        return

    # Exclude all empty rows
    data = data.where(data.notnull(), None)

    all_ok = True
    inactive_refs = []
    created_count = 0

    for i, row in enumerate(data.transpose().to_dict().values()):
        # Fill the is_active field from other fields if necessary
        row["is_active"] = is_active(row)

        update_dict = {}

        for key, value in row.items():
            enum_key = FieldType.value_dict[key]
            if enum_key in FIELD_MAPPINGS:
                update_dict[FIELD_MAPPINGS[enum_key]] = value

        print(update_dict)

        print(row)
        if row["is_active"]:
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
            except (
                ValueError,
                phonenumbers.NumberParseException,
                ValidationError,
            ) as e:
                messages.error(
                    request,
                    _(f"Failed to import {model._meta.verbose_name} {row}:\n{e}"),
                    fail_silently=True,
                )
                all_ok = False

    #         # Ensure that newly set primary group is also in member_of
    #         if (
    #             person.primary_group
    #             and person.primary_group not in person.member_of.all()
    #         ):
    #             person.member_of.add(person.primary_group)
    #             person.save()
    #
    #         if created:
    #             created_count += 1
    #     else:
    #         # Store import refs to deactivate later
    #         inactive_refs.append(person_row["import_ref"])
    #
    # # Deactivate all persons that existed but are now inactive
    # if inactive_refs:
    #     affected = Person.objects.filter(
    #         import_ref_csv__in=inactive_refs, is_active=True
    #     ).update(is_active=False)
    #
    #     if affected:
    #         messages.warning(
    #             request, _("%d existing persons were deactivated.") % affected
    #         )
    #
    # if created_count:
    #     messages.success(request, _("%d persons were newly created.") % created_count)
    #
    # if all_ok:
    #     messages.success(request, _("All persons were imported successfully."))
    # else:
    #     messages.warning(request, _("Some persons failed to be imported."))
