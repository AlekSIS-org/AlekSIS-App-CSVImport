from datetime import date

from phonenumbers import PhoneNumber

from aleksis.apps.csv_import.util.converters import (
    parse_comma_separated_data,
    parse_dd_mm_yyyy,
    parse_phone_number,
    parse_sex,
)


def test_parse_phone_number():
    fake_number = PhoneNumber(country_code=49, national_number=1635550217)
    assert parse_phone_number("+49-163-555-0217") == fake_number
    assert parse_phone_number("+491635550217") == fake_number
    assert parse_phone_number("0163-555-0217") == fake_number
    assert parse_phone_number("01635550217") == fake_number


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
    assert parse_dd_mm_yyyy("12.01.2020") == date(2020, 1, 12)
    assert parse_dd_mm_yyyy("12.12.1912") == date(1912, 12, 12)


def test_parse_dd_mm_yyyy_none():
    assert parse_dd_mm_yyyy("") is None
    assert parse_dd_mm_yyyy("foo") is None
    assert parse_dd_mm_yyyy("12.14.1912") is None


def test_parse_comma_separated_data():
    assert parse_comma_separated_data("1,2,3") == ["1", "2", "3"]
    assert parse_comma_separated_data("1,1") == ["1", "1"]
    assert parse_comma_separated_data(",1") == ["1"]
    assert parse_comma_separated_data("1") == ["1"]
    assert parse_comma_separated_data(" 2, 3") == [" 2", " 3"]


def test_parse_comma_separated_data_none():
    assert parse_comma_separated_data(",") == []
    assert parse_comma_separated_data("") == []
