import os
from typing import Sequence

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.db.models import Model

import toml

from .field_types import FieldType, field_type_registry
from .models import ImportTemplate, ImportTemplateField


def update_or_create_template(
    model: Model,
    name: str,
    verbose_name: str,
    extra_args: dict,
    fields: Sequence[FieldType],
):
    """Update or create an import template in database."""
    ct = ContentType.objects.get_for_model(model)
    template, updated = ImportTemplate.objects.update_or_create(
        name=name,
        defaults={"verbose_name": verbose_name, "content_type": ct, **extra_args},
    )

    for i, field in enumerate(fields):
        ImportTemplateField.objects.update_or_create(
            template=template, index=i, defaults={"field_type": field.name},
        )

    ImportTemplateField.objects.filter(template=template, index__gt=i).delete()


def update_or_create_default_templates():
    """Update or create default import templates."""
    template_defs = toml.load(
        os.path.join(os.path.dirname(__file__), "default_templates.toml")
    )

    for name, defs in template_defs.items():
        model = apps.get_model(defs["model"])
        fields = [
            field_type_registry.get_from_name(field_type)
            for field_type in defs["fields"]
        ]

        update_or_create_template(
            model,
            name=name,
            verbose_name=defs.get("verbose_name", ""),
            extra_args=defs.get("extra_args", {}),
            fields=fields,
        )
