from typing import Optional, Sequence

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


def create_department_groups(subjects: Sequence[str]) -> Sequence[Group]:
    """Create department groups for subjects."""
    group_type = get_site_preferences()["csv_import__group_type_departments"]
    group_prefix = get_site_preferences()["csv_import__group_prefix_departments"]

    groups = []
    for subject_name in subjects:
        # Get department subject
        subject, __ = Subject.objects.get_or_create(
            short_name=subject_name, defaults={"name": subject_name}
        )

        # Get department group
        group, __ = Group.objects.get_or_create(
            subject__subject=subject,
            group_type=group_type,
            defaults={
                "short_name": subject.short_name,
                "name": with_prefix(group_prefix, subject.name,),
            },
        )
        groups.append(group)
    return groups
