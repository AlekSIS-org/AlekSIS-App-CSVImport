from django.utils.translation import gettext as _

from dynamic_preferences.preferences import Section
from dynamic_preferences.types import ModelChoicePreference, StringPreference

from aleksis.core.models import Group, GroupType
from aleksis.core.registries import site_preferences_registry

csv_import = Section("csv_import", verbose_name=_("CSV import"))


@site_preferences_registry.register
class GroupTypeDepartments(ModelChoicePreference):
    section = csv_import
    name = "group_type_departments"
    required = False
    default = None
    model = GroupType
    verbose_name = _("Group type for department groups")
    help_text = _("If you leave it empty, no group type will be used.")


@site_preferences_registry.register
class GroupPrefixDepartments(StringPreference):
    section = csv_import
    name = "group_prefix_departments"
    default = ""
    verbose_name = _("Prefix for long names of department groups")
    help_text = _("If you leave it empty, no prefix will be added.")


@site_preferences_registry.register
class GroupGuardians(ModelChoicePreference):
    section = csv_import
    name = "group_guardians"
    required = False
    default = None
    model = Group
    verbose_name = _("Group for guardians")
    help_text = _("If you leave it empty, no group will be used.")
