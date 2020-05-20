from typing import Sequence

from django.contrib.contenttypes.models import ContentType
from django.db.models import Model
from django.utils.translation import gettext as _

from aleksis.apps.csv_import.models import (
    FieldType,
    ImportTemplate,
    ImportTemplateField,
)
from aleksis.core.models import Person


def update_or_create_template(
    model: Model, name: str, verbose_name: str, extra_args: dict, fields: Sequence
):
    """Update or create an import template in database."""

    ct = ContentType.objects.get_for_model(model)
    template, updated = ImportTemplate.objects.update_or_create(
        name=name,
        defaults={"verbose_name": verbose_name, "content_type": ct, **extra_args},
    )

    for i, field in enumerate(fields):
        ImportTemplateField.objects.update_or_create(
            template=template, index=i, defaults={"field_type": field},
        )

    ImportTemplateField.objects.filter(template=template, index__gt=i).delete()


def update_or_create_default_templates():
    """Update or create default import templates."""

    update_or_create_template(
        Person,
        name="pedasos_teachers",
        verbose_name=_("Pedasos: Teachers"),
        extra_args={"has_header_row": True, "separator": "\t"},
        fields=[
            FieldType.SHORT_NAME,
            FieldType.LAST_NAME,
            FieldType.FIRST_NAME,
            FieldType.DATE_OF_BIRTH_DD_MM_YYYY,
            FieldType.SEX,
            FieldType.DEPARTMENTS,
            FieldType.IGNORE,
        ],
    )
