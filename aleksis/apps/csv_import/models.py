from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext as _

from aleksis.core.mixins import ExtensibleModel
from aleksis.core.models import Person, Group


class FieldType(models.TextChoices):
    UNIQUE_REFERENCE = "unique_reference", _("Unique reference")
    IS_ACTIVE = "is_active", _("Is active?")
    FIRST_NAME = "first_name", _("First name")
    LAST_NAME = "last_name", _("Last name")
    ADDITIONAL_NAME = "additional_name", _("Additional name")
    SHORT_NAME = "short_name", _("Short name")
    EMAIL = "email", _("Email")
    DATE_OF_BIRTH = "date_of_birth", _("Date of birth")
    SEX = "sex", _("Sex")
    STREET = "street", _("Street")
    HOUSENUMBER = "housenumber", _("Housenumber")
    POSTAL_CODE = "postal_code", _("Postal code")
    PLACE = "place", _("Place")
    PHONE_NUMBER = "phone_number", _("Phone number")
    MOBILE_NUMBER = "mobile_number", _("Mobile number")
    IGNORE = "ignore", _("Ignore data in this field")


ALLOWED_CONTENT_TYPES = [Person, Group]


def limit_content_types():
    """Get all allowed content types."""
    ids = []
    for model in ALLOWED_CONTENT_TYPES:
        ct = ContentType.objects.get_for_model(model)
        ids.append(ct.pk)

    return {"pk__in": ids}


class ImportTemplate(ExtensibleModel):
    content_type = models.ForeignKey(
        ContentType,
        models.CASCADE,
        verbose_name=_("Content type"),
        limit_choices_to=limit_content_types,
    )
    name = models.CharField(max_length=255, verbose_name=_("Name"), unique=True)
    verbose_name = models.CharField(max_length=255, verbose_name=_("Name"))

    has_header_row = models.BooleanField(
        default=True, verbose_name=_("Has the CSV file a own header row?")
    )

    class Meta:
        ordering = ["name"]
        verbose_name = _("Import template")
        verbose_name_plural = _("Import templates")


class ImportTemplateField(ExtensibleModel):
    index = models.IntegerField(verbose_name=_("Index"))
    template = models.ForeignKey(
        ImportTemplate,
        models.CASCADE,
        verbose_name=_("Import template"),
        related_name="fields",
    )
    field_type = models.CharField(
        max_length=255, verbose_name=_("Field type"), choices=FieldType.choices
    )

    class Meta:
        ordering = ["template", "index"]
        unique_together = ["template", "index"]
        verbose_name = _("Import template field")
        verbose_name_plural = _("Import template fields")
