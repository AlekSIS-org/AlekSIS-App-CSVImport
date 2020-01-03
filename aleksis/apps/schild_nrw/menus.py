from django.utils.translation import ugettext_lazy as _

MENUS = {
    "DATA_MANAGEMENT_MENU": [
        {
            "name": _("SchILD-NRW import"),
            "url": "schild_import",
            "validators": [
                "menu_generator.validators.is_authenticated",
                "menu_generator.validators.is_superuser",
                "biscuit.core.util.core_helpers.has_person",
            ],
        }
    ]
}
