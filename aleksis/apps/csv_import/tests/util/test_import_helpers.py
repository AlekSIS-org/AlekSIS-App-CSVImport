from aleksis.apps.csv_import.util.import_helpers import has_is_active_field, is_active, with_prefix
from aleksis.core.models import Group, GroupType, Person


def test_is_active():
    row = {"is_active": True}
    assert is_active(row)
    row = {"is_active": False}
    assert not is_active(row)
    assert is_active({})


def test_has_is_active_field():
    assert has_is_active_field(Person)
    assert not has_is_active_field(Group)
    assert not has_is_active_field(GroupType)


def test_with_prefix():
    assert with_prefix("Foo", "Bar") == "Foo Bar"
    assert with_prefix("", "Bar") == "Bar"
    assert with_prefix(None, "Bar") == "Bar"
    assert with_prefix(None, "") == ""
    assert with_prefix("", "") == ""
