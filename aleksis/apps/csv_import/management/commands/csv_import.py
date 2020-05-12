from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _

from aleksis.apps.csv_import.util import schild_import_csv


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("teachers_csv_path", help=_("Path to CSV file with exported teachers"))
        parser.add_argument("students_csv_path", help=_("Path to CSV file with exported students"))
        parser.add_argument(
            "guardians_csv_path", help=_("Path to CSV file with exported guardians")
        )

    def handle(self, *args, **options):
        teachers_csv = open(options["teachers_csv_path"], "rb")
        students_csv = open(options["students_csv_path"], "rb")
        guardians_csv = open(options["guardians_csv_path"], "rb")

        schild_import_csv(None, teachers_csv, students_csv, guardians_csv)
