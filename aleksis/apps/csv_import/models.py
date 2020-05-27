from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.decorators import classproperty
from django.utils.translation import gettext as _

from aleksis.core.mixins import ExtensibleModel
from aleksis.core.models import Group, Person


class FieldType(models.TextChoices):
    UNIQUE_REFERENCE = "unique_reference", _("Unique reference")
    IS_ACTIVE = "is_active", _("Is active? (0/1)")
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

    IS_ACTIVE_SCHILD_NRW_STUDENTS = (
        "is_active_schild_nrw_students",
        _("Is active? (SchILD-NRW: students)"),
    )
    DEPARTMENTS = "departments", _("Comma-separated list of departments")
    DATE_OF_BIRTH_DD_MM_YYYY = (
        "date_of_birth_dd_mm_yyy",
        _("Date of birth (DD.MM.YYYY)"),
    )

    @classproperty
    def value_dict(cls):  # noqa
        return {member.value: member for member in cls}


# All fields that can be mapped directly to database
FIELD_MAPPINGS = {
    FieldType.UNIQUE_REFERENCE: "import_ref_csv",
    FieldType.IS_ACTIVE: "is_active",
    FieldType.FIRST_NAME: "first_name",
    FieldType.LAST_NAME: "last_name",
    FieldType.ADDITIONAL_NAME: "additional_name",
    FieldType.SHORT_NAME: "short_name",
    FieldType.EMAIL: "email",
    FieldType.DATE_OF_BIRTH: "date_of_birth",
    FieldType.SEX: "sex",
    FieldType.STREET: "street",
    FieldType.HOUSENUMBER: "housenumber",
    FieldType.POSTAL_CODE: "postal_code",
    FieldType.PLACE: "place",
    FieldType.PHONE_NUMBER: "phone_number",
    FieldType.MOBILE_NUMBER: "mobile_number",
    FieldType.IS_ACTIVE_SCHILD_NRW_STUDENTS: "is_active",
    FieldType.DATE_OF_BIRTH_DD_MM_YYYY: "date_of_birth",
}

# All other fields will use str
DATA_TYPES = {
    FieldType.IS_ACTIVE: bool,
    FieldType.IS_ACTIVE_SCHILD_NRW_STUDENTS: int,
}

ALLOWED_MODELS = [Person, Group]
ALLOWED_FIELD_TYPES_FOR_MODELS = {
    Person: {
        FieldType.UNIQUE_REFERENCE,
        FieldType.IS_ACTIVE,
        FieldType.FIRST_NAME,
        FieldType.LAST_NAME,
        FieldType.ADDITIONAL_NAME,
        FieldType.SHORT_NAME,
        FieldType.EMAIL,
        FieldType.DATE_OF_BIRTH,
        FieldType.SEX,
        FieldType.STREET,
        FieldType.HOUSENUMBER,
        FieldType.POSTAL_CODE,
        FieldType.PLACE,
        FieldType.PHONE_NUMBER,
        FieldType.MOBILE_NUMBER,
        FieldType.IGNORE,
        FieldType.IS_ACTIVE_SCHILD_NRW_STUDENTS,
        FieldType.DEPARTMENTS,
        FieldType.DATE_OF_BIRTH_DD_MM_YYYY,
    },
    Group: {FieldType.UNIQUE_REFERENCE, FieldType.SHORT_NAME, FieldType.IGNORE,},
}

SEPARATOR_CHOICES = [
    (",", ","),
    (";", ";"),
    ("\\s+", _("Whitespace")),
    ("\t", _("Tab")),
]


def get_allowed_content_types_query():
    """Get all allowed content types."""
    ids = []
    for model in ALLOWED_MODELS:
        ct = ContentType.objects.get_for_model(model)
        ids.append(ct.pk)

    return {"pk__in": ids}


class ImportTemplate(ExtensibleModel):
    content_type = models.ForeignKey(
        ContentType,
        models.CASCADE,
        verbose_name=_("Content type"),
        limit_choices_to=get_allowed_content_types_query,
    )
    name = models.CharField(max_length=255, verbose_name=_("Name"), unique=True)
    verbose_name = models.CharField(max_length=255, verbose_name=_("Name"))

    has_header_row = models.BooleanField(
        default=True, verbose_name=_("Has the CSV file a own header row?")
    )
    separator = models.CharField(
        max_length=255,
        choices=SEPARATOR_CHOICES,
        default=",",
        verbose_name=_("CSV separator"),
    )

    def __str__(self):
        return self.verbose_name

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

    @property
    def field_type_enum(self):
        return FieldType.value_dict[self.field_type]

    def clean(self):
        """Validate correct usage of field types."""
        model = self.template.content_type.model_class()
        if self.field_type not in ALLOWED_FIELD_TYPES_FOR_MODELS[model]:
            raise ValidationError(
                _("You are not allowed to use this field type in this model.")
            )

    class Meta:
        ordering = ["template", "index"]
        unique_together = ["template", "index"]
        verbose_name = _("Import template field")
        verbose_name_plural = _("Import template fields")
