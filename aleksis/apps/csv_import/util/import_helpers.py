from typing import Optional

from django.db.models import Model

from aleksis.apps.csv_import.models import ALLOWED_FIELD_TYPES, FieldType
from aleksis.apps.csv_import.settings import STATE_ACTIVE


def is_active(row: dict) -> bool:
    """Find out whether an imported object is active."""
    if "is_active" in row:
        return row["is_active"] in STATE_ACTIVE

    return True


def has_is_active_field(model: Model) -> bool:
    """Check if this model allows importing the is_active status."""
    if model in ALLOWED_FIELD_TYPES:
        if FieldType.IS_ACTIVE in ALLOWED_FIELD_TYPES[model]:
            return True
    return False


def with_prefix(prefix: Optional[str], value: str) -> str:
    """Add prefix to string.

    If prefix is not empty, this function will add a
    prefix to a string, delimited by a white space.
    """
    prefix = prefix.strip()
    if prefix:
        return f"{prefix} {value}"
    else:
        return value
