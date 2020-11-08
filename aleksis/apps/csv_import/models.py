import codecs

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext as _

from aleksis.apps.csv_import.field_types import field_type_registry
from aleksis.core.mixins import ExtensibleModel
from aleksis.core.models import Group, GroupType


def get_allowed_content_types_query():
    """Get all allowed content types."""
    ids = []
    for model in field_type_registry.allowed_models:
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
        default=True, verbose_name=_("Has the CSV file an own header row?")
    )
    separator = models.CharField(
        max_length=255,
        default=",",
        verbose_name=_("CSV separator"),
        help_text=_("For whitespace use \\\\s+, for tab \\\\t"),
    )

    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_("Base group"),
        help_text=_(
            "If imported objects are persons, they all will be members of this group after import."
        ),
    )
    group_type = models.ForeignKey(
        GroupType,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_("Group type"),
        help_text=_(
            "If imported objects are groups, they all will get this group type after import."
        ),
    )

    @property
    def parsed_separator(self):
        return codecs.escape_decode(bytes(self.separator, "utf-8"))[0].decode("utf-8")

    def save(self, *args, **kwargs):
        if not self.content_type.model == "person":
            self.group = None
        if not self.content_type.model == "group":
            self.group_type = None
        super().save(*args, **kwargs)

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
        max_length=255,
        verbose_name=_("Field type"),
        choices=field_type_registry.choices,
    )

    @property
    def field_type_class(self):
        return field_type_registry.get_from_name(self.field_type)

    def clean(self):
        """Validate correct usage of field types."""
        model = self.template.content_type.model_class()
        if (
            self.field_type
            not in field_type_registry.allowed_field_types_for_models[model]
        ):
            raise ValidationError(
                _("You are not allowed to use this field type in this model.")
            )

    class Meta:
        ordering = ["template", "index"]
        unique_together = ["template", "index"]
        verbose_name = _("Import template field")
        verbose_name_plural = _("Import template fields")
