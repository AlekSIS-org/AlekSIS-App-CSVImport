from django.utils.translation import gettext as _

from jsonstore import CharField

from aleksis.apps.csv_import.field_types import field_type_registry

for model in field_type_registry.allowed_models:
    model.field(
        import_ref_csv=CharField(verbose_name=_("CSV import reference"), blank=True)
    )
