from datetime import date
from typing import Sequence, Union

import dateparser
import phonenumbers

from aleksis.apps.csv_import.settings import SEXES
from aleksis.core.util.core_helpers import get_site_preferences


def parse_phone_number(value: str) -> Union[phonenumbers.PhoneNumber, None]:
    """Parse a phone number."""
    try:
        return phonenumbers.parse(
            value, get_site_preferences()["csv_import__phone_number_country"]
        )
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
    languages_raw = get_site_preferences()["csv_import__date_languages"]
    languages = languages_raw.split(",") if languages_raw else []
    try:
        return dateparser.parse(value, languages=languages).date()
    except (ValueError, AttributeError):
        return None


def parse_comma_separated_data(value: str) -> Sequence[str]:
    """Parse a string with comma-separated data."""
    return list(filter(lambda v: v, value.split(",")))
