from typing import Sequence

from django.contrib.contenttypes.models import ContentType
from django.db.models import Model
from django.utils.translation import gettext as _

from .field_types import (
    ShortNameFieldType,
    LastNameFieldType,
    FirstNameFieldType,
    DateOfBirthFieldType,
    SexFieldType,
    IgnoreFieldType,
    UniqueReferenceFieldType, FieldType,
)
from .models import ImportTemplate, ImportTemplateField
from aleksis.core.models import Group, Person


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
    update_or_create_template(
        Person,
        name="pedasos_teachers",
        verbose_name=_("Pedasos: Teachers"),
        extra_args={"has_header_row": True, "separator": "\t"},
        fields=[
            ShortNameFieldType,
            LastNameFieldType,
            FirstNameFieldType,
            DateOfBirthFieldType,
            SexFieldType,
            IgnoreFieldType,  # DEPARTMENTS
            IgnoreFieldType,  # IGNORE
        ],
    )
    update_or_create_template(
        Group,
        name="pedasos_classes",
        verbose_name=_("Pedasos: Classes"),
        extra_args={"has_header_row": True, "separator": "\t"},
        fields=[
            ShortNameFieldType,
            IgnoreFieldType,  # GROUP_OWNER_BY_SHORT_NAME
            IgnoreFieldType,  # GROUP_OWNER_BY_SHORT_NAME
        ],
    )
    update_or_create_template(
        Group,
        name="pedasos_courses",
        verbose_name=_("Pedasos: Courses"),
        extra_args={"has_header_row": True, "separator": "\t"},
        fields=[
            ShortNameFieldType,
            IgnoreFieldType,  # PEDASOS_CLASS_RANGE
            IgnoreFieldType,  # SUBJECT_BY_SHORT_NAME
            IgnoreFieldType,  # GROUP_OWNER_BY_SHORT_NAME
        ],
    )
    update_or_create_template(
        Person,
        name="pedasos_students",
        verbose_name=_("Pedasos: Students"),
        extra_args={"has_header_row": True, "separator": "\t"},
        fields=[
            UniqueReferenceFieldType,
            LastNameFieldType,
            FirstNameFieldType,
            DateOfBirthFieldType,
            SexFieldType,
            IgnoreFieldType,  # PRIMARY_GROUP_BY_SHORT_NAME
            IgnoreFieldType,  # MOTHER GUARDIAN_LAST_NAME GUARDIAN_FIRST_NAME GUARDIAN_EMAIL
            IgnoreFieldType,
            IgnoreFieldType,
            IgnoreFieldType,  # FATHER
            IgnoreFieldType,
            IgnoreFieldType,
            IgnoreFieldType,  # Course 1
            IgnoreFieldType,
            IgnoreFieldType,
            IgnoreFieldType,
            IgnoreFieldType,  # Course 5
            IgnoreFieldType,
            IgnoreFieldType,
            IgnoreFieldType,
            IgnoreFieldType,
            IgnoreFieldType,  # Course 10
            IgnoreFieldType,
            IgnoreFieldType,
            IgnoreFieldType,
            IgnoreFieldType,
            IgnoreFieldType,  # Course 15
            IgnoreFieldType,
            IgnoreFieldType,
            IgnoreFieldType,
            IgnoreFieldType,
            IgnoreFieldType,  # Course 20
            IgnoreFieldType,  # Course 21
        ],
    )
