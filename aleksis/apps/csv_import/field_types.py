from collections import OrderedDict
from typing import Sequence, Tuple, Optional, Callable, Type
from uuid import uuid4

from django.db.models import Model
from django.utils.decorators import classproperty

from aleksis.apps.csv_import.util.converters import parse_phone_number, parse_sex, parse_date
from aleksis.core.models import Group, Person
from django.utils.translation import gettext as _


class FieldType:
    name: str = ""
    verbose_name: str = ""
    models: Sequence = []
    data_type: type = str
    converter: Optional[Callable] = None
    alternative: Optional[str] = None

    @classproperty
    def column_name(cls) -> str:
        return cls.name


class MatchFieldType(FieldType):
    """Field type for getting an instance."""

    db_field: str = ""
    priority: int = 1


class DirectMappingFieldType(FieldType):
    """Set value directly in DB."""

    db_field: str = ""


class ProcessFieldType(FieldType):
    """Field type with custom logic for importing."""

    def process(self, instance: Model, value):
        pass


class MultipleValuesFieldType(ProcessFieldType):
    """Has multiple columns."""

    def process(self, instance: Model, values: Sequence):
        pass

    @classproperty
    def column_name(cls) -> str:
        return f"{cls.name}_{uuid4()}"


class FieldTypeRegistry:
    def __init__(self):
        self.field_types = {}
        self.allowed_field_types_for_models = {}
        self.allowed_models = set()
        self.converters = {}
        self.alternatives = {}
        self.match_field_types = []

    def register(self, field_type: Type[FieldType]):
        """Add new :class:`FieldType` to registry.

        Can be used as decorator, too.
        """
        if field_type.name in self.field_types:
            raise ValueError(f"The field type {field_type.name} is already registered.")
        self.field_types[field_type.name] = field_type

        for model in field_type.models:
            self.allowed_field_types_for_models.setdefault(model, []).append(field_type)
            self.allowed_models.add(model)

        if field_type.converter:
            self.converters[field_type.name] = field_type.converter

        if field_type.alternative:
            self.alternatives[field_type] = field_type.alternative

        if issubclass(field_type, MatchFieldType):
            self.match_field_types.append((field_type.priority, field_type))
        return field_type

    def get_from_name(self, name: str) -> FieldType:
        """Get :class:`FieldType` by its name."""
        return self.field_types[name]

    @property
    def choices(self) -> Sequence[Tuple[str, str]]:
        """Return choices in Django format."""
        return [(f.name, f.verbose_name) for f in self.field_types.values()]

    @property
    def unique_references_by_priority(self) -> Sequence[FieldType]:
        return sorted(self.match_field_types)


field_type_registry = FieldTypeRegistry()


class UniqueReferenceFieldType(MatchFieldType):
    name = "unique_reference"
    verbose_name = _("Unique reference")
    models = [Person, Group]
    db_field = "import_ref_csv"
    priority = 10


field_type_registry.register(UniqueReferenceFieldType)


@field_type_registry.register
class IsActiveFieldType(DirectMappingFieldType):
    name = "is_active"
    verbose_name = _("Is active? (0/1)")
    models = [Person]
    db_field = "is_active"
    data_type = bool


@field_type_registry.register
class NameFieldType(DirectMappingFieldType):
    name = "name"
    verbose_name = _("Name")
    models = [Group]
    db_field = "name"
    alternative = "short_name"


@field_type_registry.register
class FirstNameFieldType(DirectMappingFieldType):
    name = "first_name"
    verbose_name = _("First name")
    models = [Person]
    db_field = "first_name"


@field_type_registry.register
class LastNameFieldType(DirectMappingFieldType):
    name = "last_name"
    verbose_name = _("Last name")
    models = [Person]
    db_field = "last_name"


@field_type_registry.register
class AdditionalNameFieldType(DirectMappingFieldType):
    name = "additional_name"
    verbose_name = _("Additional name")
    models = [Person]
    db_field = "additional_name"


@field_type_registry.register
class ShortNameFieldType(MatchFieldType):
    name = "short_name"
    verbose_name = _("Short name")
    models = [Person, Group]
    priority = 8
    db_field = "short_name"
    alternative = "name"


@field_type_registry.register
class EmailFieldType(DirectMappingFieldType):
    name = "email"
    verbose_name = _("Email")
    models = [Person]
    db_field = "email"


@field_type_registry.register
class DateOfBirthFieldType(DirectMappingFieldType):
    name = "date_of_birth"
    verbose_name = _("Date of birth")
    models = [Person]
    db_field = "date_of_birth"
    converter = parse_date


@field_type_registry.register
class SexFieldType(DirectMappingFieldType):
    name = "sex"
    verbose_name = _("Sex")
    models = [Person]
    db_field = "sex"
    converter = parse_sex


@field_type_registry.register
class StreetFieldType(DirectMappingFieldType):
    name = "street"
    verbose_name = _("Street")
    models = [Person]
    db_field = "street"


@field_type_registry.register
class HouseNumberFieldType(DirectMappingFieldType):
    name = "housenumber"
    verbose_name = _("Housenumber")
    models = [Person]
    db_field = "housenumber"


@field_type_registry.register
class PostalCodeFieldType(DirectMappingFieldType):
    name = "postal_code"
    verbose_name = _("Postal code")
    models = [Person]
    db_field = "postal_code"


@field_type_registry.register
class PlaceFieldType(DirectMappingFieldType):
    name = "place"
    verbose_name = _("Place")
    models = [Person]
    db_field = "place"


@field_type_registry.register
class PhoneNumberFieldType(DirectMappingFieldType):
    name = "phone_number"
    verbose_name = _("Phone number")
    models = [Person]
    db_field = "phone_number"
    converter = parse_phone_number


@field_type_registry.register
class MobileNumberFieldType(DirectMappingFieldType):
    name = "mobile_number"
    verbose_name = _("Mobile number")
    models = [Person]
    db_field = "mobile_number"
    converter = parse_phone_number


@field_type_registry.register
class IgnoreFieldType(FieldType):
    name = "ignore"
    verbose_name = _("Ignore data in this field")
    models = [Person, Group]

    @classproperty
    def column_name(cls) -> str:
        return f"_ignore_{uuid4()}"
