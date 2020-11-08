from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _

from aleksis.apps.csv_import.models import ImportTemplate
from aleksis.apps.csv_import.util.process import import_csv
from aleksis.core.util import messages


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "csv_path", help=_("Path to CSV file with exported teachers"), required=True
        )
        parser.add_argument(
            "template",
            help=_("Name of import template which should be used"),
            required=True,
        )

    def handle(self, *args, **options):
        template_name = options["template"]
        try:
            template = ImportTemplate.objects.get(name=template_name).pk
        except ImportTemplate.DoesNotExist:
            messages.error(None, _("The provided template does not exist."))
            return

        import_csv(None, template, options["csv_path"])
