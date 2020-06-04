import pytest

from aleksis.apps.csv_import.util.import_helpers import bulk_get_or_create
from aleksis.core.models import Person

pytestmark = pytest.mark.django_db


def test_bulk_get_or_create_person():
    short_names = ["FOO", "BAR", "BAZ"]

    # with pytest.raises(Ex)
    r = bulk_get_or_create(Person, short_names, "short_name")
    assert sorted([x.short_name for x in r]) == sorted(short_names)

    r = bulk_get_or_create(Person, short_names, "short_name")
    assert sorted([x.short_name for x in r]) == sorted(short_names)


def test_bulk_get_or_create_person_default_attrs():
    short_names = ["FOO", "BAR", "BAZ"]

    r = bulk_get_or_create(Person, short_names, "short_name", default_attrs="last_name")

    for person in r:
        assert person.short_name in short_names
        assert person.short_name == person.last_name


def test_bulk_get_or_create_person_default_attrs_list():
    short_names = ["FOO", "BAR", "BAZ"]

    r = bulk_get_or_create(
        Person, short_names, "short_name", default_attrs=["first_name", "last_name"]
    )

    for person in r:
        assert person.short_name == person.last_name
        assert person.short_name == person.first_name


def test_bulk_get_or_create_person_defaults():
    short_names = ["FOO", "BAR", "BAZ"]

    defaults = {"first_name": "foo", "last_name": "bar"}

    r = bulk_get_or_create(Person, short_names, "short_name", defaults=defaults)

    for person in r:
        assert person.first_name == "foo"
        assert person.last_name == "bar"


def test_bulk_get_or_create_person_defaults_default_attrs():
    short_names = ["FOO", "BAR", "BAZ"]

    defaults = {"last_name": "foo"}

    r = bulk_get_or_create(
        Person,
        short_names,
        "short_name",
        default_attrs=["first_name"],
        defaults=defaults,
    )

    for person in r:
        assert person.short_name == person.first_name
        assert person.last_name == "foo"
