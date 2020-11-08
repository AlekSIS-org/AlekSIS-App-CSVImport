from datetime import date

import pytest
from phonenumbers import PhoneNumber

from aleksis.apps.csv_import.util.converters import (
    parse_comma_separated_data,
    parse_date,
    parse_phone_number,
    parse_sex,
)
from aleksis.core.util.core_helpers import get_site_preferences

pytestmark = pytest.mark.django_db


def test_parse_phone_number():
    get_site_preferences()["csv_import__phone_number_country"] = "DE"
    fake_number = PhoneNumber(country_code=49, national_number=1635550217)
    assert parse_phone_number("+49-163-555-0217") == fake_number
    assert parse_phone_number("+491635550217") == fake_number
    assert parse_phone_number("0163-555-0217") == fake_number
    assert parse_phone_number("01635550217") == fake_number
    get_site_preferences()["csv_import__phone_number_country"] = "GB"
    assert parse_phone_number("0163-555-0217") != fake_number
    assert parse_phone_number("01635550217") != fake_number


def test_parse_phone_number_none():
    assert parse_phone_number("") is None
    assert parse_phone_number("foo") is None


def test_parse_sex():
    assert parse_sex("w") == "f"
    assert parse_sex("W") == "f"
    assert parse_sex("m") == "m"
    assert parse_sex("M") == "m"
    assert parse_sex("weiblich") == "f"
    assert parse_sex("Weiblich") == "f"
    assert parse_sex("männlich") == "m"
    assert parse_sex("Männlich") == "m"


def test_parse_sex_none():
    assert parse_sex("") == ""
    assert parse_sex("foo") == ""


def test_parse_dd_mm_yyyy():
    get_site_preferences()["csv_import__date_languages"] = "de"
    assert parse_date("12.01.2020") == date(2020, 1, 12)
    assert parse_date("12.12.1912") == date(1912, 12, 12)
    get_site_preferences()["csv_import__date_languages"] = "en-US"
    assert parse_date("12.01.2020") != date(2020, 1, 12)
    assert parse_date("12.12.1912") != date(1912, 12, 12)


def test_parse_dd_mm_yyyy_none():
    assert parse_date("") is None
    assert parse_date("foo") is None
    assert parse_date("12.143.1912") is None


def test_parse_date_iso():
    get_site_preferences()["csv_import__date_languages"] = ""
    assert parse_date("2020-11-12") == date(2020, 11, 12)


def test_parse_date_en():
    get_site_preferences()["csv_import__date_languages"] = ""
    assert parse_date("11/12/2020") == date(2020, 11, 12)
    get_site_preferences()["csv_import__date_languages"] = "de"
    assert parse_date("11/12/2020") != date(2020, 11, 12)


def test_parse_comma_separated_data():
    assert parse_comma_separated_data("1,2,3") == ["1", "2", "3"]
    assert parse_comma_separated_data("1,1") == ["1", "1"]
    assert parse_comma_separated_data(",1") == ["1"]
    assert parse_comma_separated_data("1") == ["1"]
    assert parse_comma_separated_data(" 2, 3") == [" 2", " 3"]


def test_parse_comma_separated_data_none():
    assert parse_comma_separated_data(",") == []
    assert parse_comma_separated_data("") == []
