from datetime import date, datetime
from typing import Optional

import phonenumbers

from aleksis.apps.csv_import.models import FieldType
from aleksis.apps.csv_import.settings import PHONE_NUMBER_COUNTRY, SEXES


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


def parse_comma_separated_data(value: Optional[str]) -> list:
    """Parse a string with comma-separated data."""
    if value:
        return value.split(",")
    return []


CONVERTERS = {
    FieldType.PHONE_NUMBER.value: parse_phone_number,
    FieldType.MOBILE_NUMBER.value: parse_phone_number,
    FieldType.SEX.value: parse_sex,
    FieldType.DEPARTMENTS.value: parse_comma_separated_data,
    FieldType.DATE_OF_BIRTH_DD_MM_YYYY.value: parse_dd_mm_yyyy,
}
