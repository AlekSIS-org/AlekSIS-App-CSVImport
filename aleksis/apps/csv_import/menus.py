from django.utils.translation import gettext_lazy as _

MENUS = {
    "DATA_MANAGEMENT_MENU": [
        {
            "name": _("CSV import"),
            "url": "csv_import",
            "validators": [
                (
                    "aleksis.core.util.predicates.permission_validator",
                    "csv_import.import_data",
                ),
            ],
        }
    ]
}
