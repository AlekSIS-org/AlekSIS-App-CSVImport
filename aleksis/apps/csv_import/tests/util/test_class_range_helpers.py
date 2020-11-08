import pytest

from aleksis.apps.csv_import.util.class_range_helpers import (
    get_classes_per_grade,
    get_classes_per_short_name,
    get_grade_and_class_from_class_range,
    get_max_class,
    get_min_class,
    parse_class_range,
)
from aleksis.core.models import Group

pytestmark = pytest.mark.django_db

CLASSES = [
    "5a",
    "5b",
    "5c",
    "5d",
    "6a",
    "6b",
    "6c",
    "6d",
    "7a",
    "7b",
    "7c",
    "7d",
    "8a",
    "8b",
    "8c",
    "8d",
    "9a",
    "9b",
    "9c",
    "9d",
    "Ea",
    "Eb",
    "Ec",
    "Ed",
    "Q1a",
    "Q1b",
    "Q1c",
    "Q1d",
    "Q2a",
    "Q2b",
    "Q2c",
    "Q2d",
]
CLASSES_PER_GRADE = {
    "5": ["a", "b", "c", "d"],
    "6": ["a", "b", "c", "d"],
    "7": ["a", "b", "c", "d"],
    "8": ["a", "b", "c", "d"],
    "9": ["a", "b", "c", "d"],
    "E": ["a", "b", "c", "d"],
    "Q1": ["a", "b", "c", "d"],
    "Q2": ["a", "b", "c", "d"],
}
CLASSES_PER_GRADE_INCOMPLETE = {
    "5": ["a", "b", "c", "d"],
    "6": ["a", "b", "c", "d"],
    "7": ["a", "b", "c", "d"],
    "8": ["a", "b"],
    "9": ["a", "b", "c", "d"],
    "E": ["a", "b", "c", "d"],
    "Q1": ["a", "b", "c", "d"],
    "Q2": ["b", "c"],
}


def test_get_classes_per_grade():
    assert get_classes_per_grade(CLASSES) == CLASSES_PER_GRADE
    assert get_classes_per_grade(["5a", "5b", "5c", "6a", "6b", "6c", "6d"]) == {
        "5": ["a", "b", "c"],
        "6": ["a", "b", "c", "d"],
    }
    assert get_classes_per_grade([]) == {}


def test_get_min_max_class():
    assert get_min_class(CLASSES_PER_GRADE_INCOMPLETE, "5") == "a"
    assert get_max_class(CLASSES_PER_GRADE_INCOMPLETE, "5") == "d"
    assert get_min_class(CLASSES_PER_GRADE_INCOMPLETE, "8") == "a"
    assert get_max_class(CLASSES_PER_GRADE_INCOMPLETE, "8") == "b"
    assert get_min_class(CLASSES_PER_GRADE_INCOMPLETE, "Q2") == "b"
    assert get_max_class(CLASSES_PER_GRADE_INCOMPLETE, "Q2") == "c"


def test_get_grade_and_class_from_class_range():
    assert get_grade_and_class_from_class_range(CLASSES_PER_GRADE, "5-Q2") == (
        "5",
        "a",
        "Q2",
        "d",
    )
    assert get_grade_and_class_from_class_range(CLASSES_PER_GRADE, "5a-7b") == (
        "5",
        "a",
        "7",
        "b",
    )
    assert get_grade_and_class_from_class_range(CLASSES_PER_GRADE, "5a-d") == (
        "5",
        "a",
        "5",
        "d",
    )
    assert get_grade_and_class_from_class_range(CLASSES_PER_GRADE, "7-8") == (
        "7",
        "a",
        "8",
        "d",
    )


def test_get_classes_per_short_name():
    Group.objects.bulk_create([Group(short_name=name, name=name) for name in CLASSES])

    classes_per_short_name = get_classes_per_short_name(None)

    for class_ in CLASSES:
        assert class_ in classes_per_short_name
        assert classes_per_short_name[class_].short_name == class_


def test_parse_class_range():
    Group.objects.bulk_create([Group(short_name=name, name=name) for name in CLASSES])

    classes_per_short_name = get_classes_per_short_name(None)

    classes = parse_class_range(classes_per_short_name, CLASSES_PER_GRADE, "5-Q2")
    assert sorted([x.short_name for x in classes]) == CLASSES

    classes = parse_class_range(classes_per_short_name, CLASSES_PER_GRADE, "5a-d")
    assert sorted([x.short_name for x in classes]) == ["5a", "5b", "5c", "5d"]
