from django.utils.translation import gettext as _

from jsonstore import CharField

from aleksis.apps.csv_import.models import ALLOWED_CONTENT_TYPES

for model in ALLOWED_CONTENT_TYPES:
    model.field(
        import_ref_csv=CharField(verbose_name=_("CSV import reference"), null=True, blank=True)
    )
