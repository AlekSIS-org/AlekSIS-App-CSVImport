from collections import OrderedDict
from typing import Any, BinaryIO, Callable, Dict, Optional, Union
from uuid import uuid4

from django.http import HttpRequest
from django.utils.translation import gettext as _

import pandas
import phonenumbers

from aleksis.apps.csv_import.models import ImportTemplate, FieldType, DATA_TYPES
from aleksis.core.models import Person
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


def import_csv(
    request: Union[HttpRequest, None],
    template: ImportTemplate,
    csv: Union[BinaryIO, str],
) -> None:
    csv_converters = {
        "phone_number": parse_phone_number,
        "mobile_number": parse_phone_number,
        "sex": parse_sex,
    }

    cols = []
    for field in template.fields.all():
        # Get data type
        if field.field_type in DATA_TYPES:
            data_type = DATA_TYPES[field.field_type]
        else:
            # Use string if no data type is provided
            data_type = str

        # Get column header
        if field.field_type == FieldType.IGNORE:
            # Create random header for ignoring (leading _)
            key = f"_ignore_{uuid4()}"
        else:
            # Use key of enum for other data types
            key = field.field_type.value

        cols.append((key, data_type))

    cols = OrderedDict(cols)

    data = pandas.read_csv(
        csv,
        sep=";",
        names=cols.keys(),
        dtype=cols,
        usecols=lambda k: not k.startswith("_"),
        keep_default_na=False,
        converters=csv_converters,
        parse_dates=DATE_FIELDS,
        quotechar='"',
        encoding="utf-8-sig",
        true_values=TRUE_VALUES,
        false_values=FALSE_VALUES,
    )

    # Clean up invalid date values
    data.date_of_birth = data.date_of_birth.astype(object)

    # Exclude all empty rows
    data = data.where(data.notnull(), None)

    all_ok = True
    inactive_refs = []
    created_count = 0

    for person_row in data.transpose().to_dict().values():
        # Fill the is_active field from other fields if necessary
        person_row["is_active"] = is_active(person_row)

        if person_row["is_active"]:
            created = False
            try:
                person, created = Person.objects.update_or_create(
                    import_ref=person_row["import_ref"], defaults=person_row
                )
            except (ValueError, phonenumbers.NumberParseException) as err:
                messages.error(
                    request,
                    _(
                        "Failed to import person %s"
                        % (
                            "%s, %s"
                            % (person_row["last_name"], person_row["first_name"])
                        )
                    )
                    + ": %s" % err,
                    fail_silently=True,
                )
                all_ok = False

            # Ensure that newly set primary group is also in member_of
            if (
                person.primary_group
                and person.primary_group not in person.member_of.all()
            ):
                person.member_of.add(person.primary_group)
                person.save()

            if created:
                created_count += 1
        else:
            # Store import refs to deactivate later
            inactive_refs.append(person_row["import_ref"])

    # Deactivate all persons that existed but are now inactive
    if inactive_refs:
        affected = Person.objects.filter(
            import_ref_csv__in=inactive_refs, is_active=True
        ).update(is_active=False)

        if affected:
            messages.warning(
                request, _("%d existing persons were deactivated.") % affected
            )

    if created_count:
        messages.success(request, _("%d persons were newly created.") % created_count)

    if all_ok:
        messages.success(request, _("All persons were imported successfully."))
    else:
        messages.warning(request, _("Some persons failed to be imported."))
