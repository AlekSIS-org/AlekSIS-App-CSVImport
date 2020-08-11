from datetime import date
from typing import Sequence, Union

import dateparser
import phonenumbers

# from aleksis.apps.csv_import.models import FieldType
from aleksis.apps.csv_import.settings import PHONE_NUMBER_COUNTRY, SEXES


def parse_phone_number(value: str) -> Union[phonenumbers.PhoneNumber, None]:
    """Parse a phone number."""
    try:
        return phonenumbers.parse(value, PHONE_NUMBER_COUNTRY)
    except phonenumbers.NumberParseException:
        return None


def parse_sex(value: str) -> str:
    """Parse sex via SEXES dictionary."""
    value = value.lower()
    if value in SEXES:
        return SEXES[value]

    return ""


def parse_date(value: str) -> Union[date, None]:
    """Parse string date."""
    try:
        return dateparser.parse(value)
    except ValueError:
        return None


def parse_comma_separated_data(value: str) -> Sequence[str]:
    """Parse a string with comma-separated data."""
    return list(filter(lambda v: v, value.split(",")))


# CONVERTERS = {
#     FieldType.PHONE_NUMBER.value: parse_phone_number,
#     FieldType.MOBILE_NUMBER.value: parse_phone_number,
#     FieldType.SEX.value: parse_sex,
#     FieldType.DEPARTMENTS.value: parse_comma_separated_data,
#     FieldType.DATE_OF_BIRTH_DD_MM_YYYY.value: parse_dd_mm_yyyy,
# }
