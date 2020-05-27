from django.utils.translation import gettext as _

from jsonstore import CharField

from aleksis.apps.csv_import.models import ALLOWED_MODELS

for model in ALLOWED_MODELS:
    model.field(
        import_ref_csv=CharField(verbose_name=_("CSV import reference"), blank=True)
    )
