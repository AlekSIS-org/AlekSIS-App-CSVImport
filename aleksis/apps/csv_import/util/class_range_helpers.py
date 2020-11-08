"""Support for parsing typical German class ranges."""

import re
from collections import OrderedDict
from typing import Dict, List, Sequence, Tuple

from aleksis.core.models import Group

REGEX_CLASS_RANGE = r"^([0-9]+|E|Q1|Q2)([a-z]?)-((?:[0-9]+|E|Q1|Q2)?)([a-z]?)"
REGEX_CLASS = r"^([0-9]+|E|Q1|Q2)([a-z])$"
REGEX_CLASS_DB = r"^([0-9]+|E|Q1|Q2)([a-z])$"


def get_classes_per_grade(classes: Sequence[str]):
    """Get classes sorted by grades.

    :param classes: List with all classes
    :return: Dict with grades as keys and class labels as items

    >>> get_classes_per_grade(["5a", "5b", "5c", "6a", "6b", "6c", "6d"])
    {'5': ['a', 'b', 'c'],
    '6': ['a', 'b', 'c', 'd']}
    """
    classes_per_grade = OrderedDict()
    for class_ in classes:
        match = re.match(REGEX_CLASS, class_)

        grade, group = match.group(1), match.group(2)

        if grade not in classes_per_grade:
            classes_per_grade[grade] = []

        if group not in classes_per_grade[grade]:
            classes_per_grade[grade].append(group)

    return classes_per_grade


def get_classes_per_short_name(school_term):
    """Get all groups which match the class range schema and group them by their short names."""
    qs = Group.objects.filter(short_name__regex=REGEX_CLASS_DB, school_term=school_term)

    return {obj.short_name: obj for obj in qs}


def get_min_class(classes_per_grade: Dict[str, Sequence[str]], grade: str):
    """Get label of first class for a grade."""
    return classes_per_grade[grade][0]


def get_max_class(classes_per_grade: Dict[str, Sequence[str]], grade: str):
    """Get label of last class for a grade."""
    return classes_per_grade[grade][-1]


def get_grade_and_class_from_class_range(
    classes_per_grade: Dict[str, Sequence[str]], class_range: str
) -> Tuple[str, str, str, str]:
    """Parse a class range into single parts (grade, class labels) and auto-fill missing parts.

    :param classes_per_grade: All available class labels grouped by grades
    :param class_range: Range to parse
    :return: Start grade, start class label, stop grade, stop class label
    """
    match = re.match(REGEX_CLASS_RANGE, class_range)

    grade_start = match.group(1)
    class_start = match.group(2)
    grade_stop = match.group(3)
    class_stop = match.group(4)

    grade_stop = grade_stop if grade_stop else grade_start

    class_start = (
        class_start if class_start else get_min_class(classes_per_grade, grade_start)
    )
    class_stop = (
        class_stop if class_stop else get_max_class(classes_per_grade, grade_stop)
    )

    return (grade_start, class_start, grade_stop, class_stop)


def parse_class_range(
    classes_per_short_name: Dict[str, Group],
    classes_per_grade: Dict[str, Sequence[str]],
    class_range: str,
) -> List[Group]:
    """Parse a class range into AlekSIS groups.

    :param classes_per_short_name: All available classes in an `OrderedDict` (key is short name)
    :param classes_per_grade: All available class labels grouped by grades
    :param class_range: Range to parse
    :return: List of AlekSIS groups
    """
    if re.match(REGEX_CLASS, class_range):
        # Single class
        return [classes_per_short_name[class_range]]
    else:
        # Class range
        (
            grade_start,
            group_start,
            grade_stop,
            group_stop,
        ) = get_grade_and_class_from_class_range(classes_per_grade, class_range)

        class_a = f"{grade_start}{group_start}"
        class_b = f"{grade_stop}{group_stop}"

        classes = list(classes_per_short_name.keys())
        i_a = classes.index(class_a)
        i_b = classes.index(class_b)

        # Get all classes in this range
        classes_tuple = list(classes_per_short_name.items())[i_a : i_b + 1]

        return [class_t[1] for class_t in classes_tuple]
