from typing import Sequence

from django.contrib.contenttypes.models import ContentType
from django.db.models import Model
from django.utils.translation import gettext as _

from aleksis.core.models import Group, Person

from .field_types import (
    ChildByUniqueReference,
    DateOfBirthFieldType,
    DepartmentsFieldType,
    EmailFieldType,
    FieldType,
    FirstNameFieldType,
    GroupMembershipByShortNameFieldType,
    GroupOwnerByShortNameFieldType,
    GroupSubjectByShortNameFieldType,
    IgnoreFieldType,
    LastNameFieldType,
    PedasosClassRangeFieldType,
    PrimaryGroupByShortNameFieldType,
    SexFieldType,
    ShortNameFieldType,
    UniqueReferenceFieldType,
)
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
            DepartmentsFieldType,
            IgnoreFieldType,
        ],
    )
    update_or_create_template(
        Group,
        name="pedasos_classes",
        verbose_name=_("Pedasos: Classes"),
        extra_args={"has_header_row": True, "separator": "\t"},
        fields=[
            ShortNameFieldType,
            GroupOwnerByShortNameFieldType,
            GroupOwnerByShortNameFieldType,
        ],
    )
    update_or_create_template(
        Group,
        name="pedasos_courses",
        verbose_name=_("Pedasos: Courses"),
        extra_args={"has_header_row": True, "separator": "\t"},
        fields=[
            ShortNameFieldType,
            PedasosClassRangeFieldType,
            GroupSubjectByShortNameFieldType,
            GroupOwnerByShortNameFieldType,
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
            PrimaryGroupByShortNameFieldType,
            IgnoreFieldType,  # MOTHER
            IgnoreFieldType,
            IgnoreFieldType,
            IgnoreFieldType,  # FATHER
            IgnoreFieldType,
            IgnoreFieldType,
            GroupMembershipByShortNameFieldType,  # Course 1
            GroupMembershipByShortNameFieldType,
            GroupMembershipByShortNameFieldType,
            GroupMembershipByShortNameFieldType,
            GroupMembershipByShortNameFieldType,  # Course 5
            GroupMembershipByShortNameFieldType,
            GroupMembershipByShortNameFieldType,
            GroupMembershipByShortNameFieldType,
            GroupMembershipByShortNameFieldType,
            GroupMembershipByShortNameFieldType,  # Course 10
            GroupMembershipByShortNameFieldType,
            GroupMembershipByShortNameFieldType,
            GroupMembershipByShortNameFieldType,
            GroupMembershipByShortNameFieldType,
            GroupMembershipByShortNameFieldType,  # Course 15
            GroupMembershipByShortNameFieldType,
            GroupMembershipByShortNameFieldType,
            GroupMembershipByShortNameFieldType,
            GroupMembershipByShortNameFieldType,
            GroupMembershipByShortNameFieldType,  # Course 20
            GroupMembershipByShortNameFieldType,  # Course 21
        ],
    )
    update_or_create_template(
        Person,
        name="pedasos_guardians_1",
        verbose_name=_("Pedasos: Guardians 1"),
        extra_args={"has_header_row": True, "separator": "\t"},
        fields=[
            ChildByUniqueReference,
            IgnoreFieldType,
            IgnoreFieldType,
            IgnoreFieldType,
            IgnoreFieldType,
            IgnoreFieldType,
            LastNameFieldType,  # MOTHER
            FirstNameFieldType,
            EmailFieldType,
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
    update_or_create_template(
        Person,
        name="pedasos_guardians_2",
        verbose_name=_("Pedasos: Guardians 2"),
        extra_args={"has_header_row": True, "separator": "\t"},
        fields=[
            ChildByUniqueReference,
            IgnoreFieldType,
            IgnoreFieldType,
            IgnoreFieldType,
            IgnoreFieldType,
            IgnoreFieldType,
            IgnoreFieldType,  # MOTHER
            IgnoreFieldType,
            IgnoreFieldType,
            LastNameFieldType,  # FATHER
            FirstNameFieldType,
            EmailFieldType,
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
