from django.utils.translation import ugettext as _

MENUS = {
    'NAV_MENU_CORE': [
        {
            'name': _('Interfaces'),
            'url': '#',
            'root': True,
            'validators': ['menu_generator.validators.is_authenticated', 'menu_generator.validators.is_superuser'],
            'submenu': [
                {
                    'name': _('SchILD-NRW import'),
                    'url': 'schild_import',
                    'validators': ['menu_generator.validators.is_authenticated', 'menu_generator.validators.is_superuser']
                }
            ]
        }
    ]
}
