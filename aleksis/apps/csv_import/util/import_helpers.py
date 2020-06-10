from typing import Optional, Sequence, Union

from django.db.models import Model

from aleksis.apps.chronos.models import Subject
from aleksis.apps.csv_import.models import ALLOWED_FIELD_TYPES_FOR_MODELS, FieldType
from aleksis.apps.csv_import.settings import STATE_ACTIVE
from aleksis.core.models import Group
from aleksis.core.util.core_helpers import get_site_preferences


def is_active(row: dict) -> bool:
    """Find out whether an imported object is active."""
    if "is_active" in row:
        return row["is_active"] in STATE_ACTIVE

    return True


def has_is_active_field(model: Model) -> bool:
    """Check if this model allows importing the is_active status."""
    if model in ALLOWED_FIELD_TYPES_FOR_MODELS:
        if FieldType.IS_ACTIVE in ALLOWED_FIELD_TYPES_FOR_MODELS[model]:
            return True
    return False


def with_prefix(prefix: Optional[str], value: str) -> str:
    """Add prefix to string.

    If prefix is not empty, this function will add a
    prefix to a string, delimited by a white space.
    """
    prefix = prefix.strip() if prefix else ""
    if prefix:
        return f"{prefix} {value}"
    else:
        return value


def get_subject_by_short_name(short_name: str) -> Subject:
    subject, __ = Subject.objects.get_or_create(
        short_name=short_name, defaults={"name": short_name}
    )
    return subject


def create_department_groups(subjects: Sequence[str]) -> Sequence[Group]:
    """Create department groups for subjects."""
    group_type = get_site_preferences()["csv_import__group_type_departments"]
    group_prefix = get_site_preferences()["csv_import__group_prefix_departments"]

    groups = []
    for subject_name in subjects:
        # Get department subject
        subject = get_subject_by_short_name(subject_name)

        # Get department group
        group, __ = Group.objects.get_or_create(
            group_type=group_type,
            short_name=subject.short_name,
            defaults={
                "subject__subject": subject,
                "name": with_prefix(group_prefix, subject.name),
            },
        )
        groups.append(group)
    return groups


def bulk_get_or_create(
    model: Model,
    objs: Sequence,
    attr: str,
    default_attrs: Optional[Union[Sequence[str], str]] = None,
    defaults: Optional[dict] = None,
) -> Sequence[Model]:
    """
    Do get_or_create on a list of values.

    :param model: Model on which get_or_create should be executed
    :param objs: List of values
    :param attr: Field of model which should be set
    :param default_attrs: One or more extra fields of model which also should be set to the value
    :param defaults: Extra fields of model which should be set to a specific value
    :return: List of instances
    """
    if not defaults:
        defaults = {}

    if not default_attrs:
        default_attrs = []

    if not isinstance(default_attrs, list):
        default_attrs = [default_attrs]

    attrs = default_attrs + [attr]

    qs = model.objects.filter(**{f"{attr}__in": objs})
    existing_values = qs.values_list(attr, flat=True)

    instances = [x for x in qs]
    for obj in objs:
        if obj in existing_values:
            continue

        kwargs = defaults
        for _attr in attrs:
            kwargs[_attr] = obj
        instance = model.objects.create(**kwargs)

        instances.append(instance)

    return instances
