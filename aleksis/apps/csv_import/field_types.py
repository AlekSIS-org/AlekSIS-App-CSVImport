from typing import Callable, Optional, Sequence, Tuple, Type
from uuid import uuid4

from django.db.models import Model
from django.utils.functional import classproperty
from django.utils.translation import gettext as _

from aleksis.apps.csv_import.util.class_range_helpers import (
    get_classes_per_grade,
    get_classes_per_short_name,
    parse_class_range,
)
from aleksis.apps.csv_import.util.converters import (
    parse_comma_separated_data,
    parse_date,
    parse_phone_number,
    parse_sex,
)
from aleksis.apps.csv_import.util.import_helpers import (
    bulk_get_or_create,
    get_subject_by_short_name,
    with_prefix,
)
from aleksis.core.models import Group, Person, SchoolTerm
from aleksis.core.util.core_helpers import get_site_preferences


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

    @classmethod
    def prepare(cls, school_term: SchoolTerm):
        cls.school_term = school_term


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
        self.process_field_types = []

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

        if issubclass(field_type, ProcessFieldType):
            self.process_field_types.append(field_type)

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
class EmailFieldType(MatchFieldType):
    name = "email"
    verbose_name = _("Email")
    models = [Person]
    db_field = "email"
    priority = 12


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


@field_type_registry.register
class DepartmentsFieldType(ProcessFieldType):
    name = "departments"
    verbose_name = _("Comma-seperated list of departments")
    models = [Person]
    converter = parse_comma_separated_data

    def process(self, instance: Model, value):
        group_type = get_site_preferences()["csv_import__group_type_departments"]
        group_prefix = get_site_preferences()["csv_import__group_prefix_departments"]

        groups = []
        for subject_name in value:
            # Get department subject
            subject = get_subject_by_short_name(subject_name)

            # Get department group
            group, __ = Group.objects.get_or_create(
                group_type=group_type,
                short_name=subject.short_name,
                defaults={"name": with_prefix(group_prefix, subject.name),},
            )
            group.subject = subject
            group.save()

            groups.append(group)

        instance.member_of.add(*groups)


@field_type_registry.register
class GroupSubjectByShortNameFieldType(ProcessFieldType):
    name = "group_subject_short_name"
    verbose_name = _("Short name of the subject")
    models = [Group]

    def process(self, instance: Model, value):
        subject = get_subject_by_short_name(value)
        instance.subject = subject
        instance.save()


@field_type_registry.register
class ClassRangeFieldType(ProcessFieldType):
    name = "class_range"
    verbose_name = _("Class range (e. g. 7a-d)")
    models = [Group]

    @classmethod
    def prepare(cls, school_term: SchoolTerm):
        """Prefetch class groups."""
        cls.classes_per_short_name = get_classes_per_short_name(school_term)
        cls.classes_per_grade = get_classes_per_grade(cls.classes_per_short_name.keys())

    def process(self, instance: Model, value):
        classes = parse_class_range(
            self.classes_per_short_name, self.classes_per_grade, value,
        )
        instance.parent_groups.set(classes)


@field_type_registry.register
class PrimaryGroupByShortNameFieldType(ProcessFieldType):
    name = "primary_group_short_name"
    verbose_name = _("Short name of the person's primary group")
    models = [Person]

    def process(self, instance: Model, value):
        try:
            group = Group.objects.get(short_name=value, school_term=self.school_term)
            instance.primary_group = group
            instance.member_of.add(group)
            instance.save()
        except Group.DoesNotExist:
            raise RuntimeError(
                _(
                    f"{instance}: Failed to import the primary group: "
                    f"Group {value} does not exist in school term {self.school_term}."
                )
            )


@field_type_registry.register
class GroupOwnerByShortNameFieldType(MultipleValuesFieldType):
    name = "group_owner_short_name"
    verbose_name = _("Short name of a single group owner")
    models = [Group]

    def process(self, instance: Model, values: Sequence):
        group_owners = bulk_get_or_create(
            Person,
            values,
            attr="short_name",
            default_attrs="last_name",
            defaults={"first_name": "?"},
        )
        instance.owners.set(group_owners)


@field_type_registry.register
class GroupMembershipByShortNameFieldType(MultipleValuesFieldType):
    name = "group_membership_short_name"
    verbose_name = _("Short name of the group the person is a member of")

    models = [Person]

    def process(self, instance: Model, values: Sequence):
        groups = Group.objects.filter(
            short_name__in=values, school_term=self.school_term
        )
        instance.member_of.add(*groups)


@field_type_registry.register
class ChildByUniqueReference(ProcessFieldType):
    name = "child_by_unique_reference"
    verbose_name = _("Child by unique reference (from students import)")
    models = [Person]

    def process(self, instance: Model, value):
        child = Person.objects.get(import_ref_csv=value)
        instance.children.add(child)
