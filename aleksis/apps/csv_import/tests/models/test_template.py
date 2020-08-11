from django.contrib.contenttypes.models import ContentType

import pytest

from aleksis.apps.csv_import.models import (
    ALLOWED_MODELS,
    FieldType,
    ImportTemplate,
    get_allowed_content_types_query,
)
from aleksis.core.models import Person

pytestmark = pytest.mark.django_db


def test_limit_content_types():
    query = get_allowed_content_types_query()
    cts = ContentType.objects.filter(**query)
    model_classes = []
    for ct in cts:
        model_classes.append(ct.model_class())
        assert ct.model_class() in ALLOWED_MODELS
    for ct in ALLOWED_MODELS:
        assert ct in model_classes


def test_import_template_str():
    template = ImportTemplate.objects.create(
        content_type=ContentType.objects.get_for_model(Person),
        name="foo",
        verbose_name="Bar",
    )
    assert str(template) == "Bar"


def test_import_template_field():
    template = ImportTemplate.objects.create(
        content_type=ContentType.objects.get_for_model(Person),
        name="foo",
        verbose_name="Bar",
    )
    field_0 = template.fields.create(field_type=FieldType.UNIQUE_REFERENCE, index=0)
    field_1 = template.fields.create(field_type=FieldType.SHORT_NAME, index=1)
    field_2 = template.fields.create(field_type=FieldType.IS_ACTIVE, index=2)

    assert field_0.field_type_class == FieldType.UNIQUE_REFERENCE
    assert field_1.field_type_class == FieldType.SHORT_NAME
    assert field_2.field_type_class == FieldType.IS_ACTIVE

    assert template.fields.count() == 3
