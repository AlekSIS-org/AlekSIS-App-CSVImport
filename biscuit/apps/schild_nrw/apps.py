from django.apps import AppConfig
from django.utils.translation import ugettext as _


class SchILDNRWConfig(AppConfig):
    name = 'biscuit.apps.schild_nrw'
    verbose_name = 'BiscuIT - ' + _('SchILD-NRW interface')
