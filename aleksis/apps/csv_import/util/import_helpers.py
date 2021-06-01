from typing import Optional, Sequence, Union

from django.db.models import Model

from aleksis.apps.csv_import.settings import STATE_ACTIVE


def is_active(row: dict) -> bool:
    """Find out whether an imported object is active."""
    if "is_active" in row:
        return row["is_active"] in STATE_ACTIVE

    return True


def has_is_active_field(model: Model) -> bool:
    """Check if this model allows importing the is_active status."""
    from aleksis.apps.csv_import.field_types import IsActiveFieldType, field_type_registry

    if model in field_type_registry.allowed_field_types_for_models:
        if IsActiveFieldType in field_type_registry.allowed_field_types_for_models[model]:
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
