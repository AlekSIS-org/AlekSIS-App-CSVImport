from django.db import ProgrammingError

from aleksis.core.util.apps import AppConfig


class CSVImportConfig(AppConfig):
    name = "aleksis.apps.csv_import"
    verbose_name = "AlekSIS — CSV import"

    urls = {
        "Repository": "https://edugit.org/AlekSIS/Onboarding/AlekSIS-App-CSVImport/",
    }
    licence = "EUPL-1.2+"
    copyright = (
        ([2019], "Dominik George", "dominik.george@teckids.org"),
        ([2019], "mirabilos", "thorsten.glaser@teckids.org"),
        ([2019], "Tom Teichler", "tom.teichler@teckids.org"),
    )

    def ready(self):
        super().ready()

        # Create default import templates
        try:
            from aleksis.apps.csv_import.templates import (
                update_or_create_default_templates,
            )  # noqa

            update_or_create_default_templates()
        except ProgrammingError:
            # Catch if there are no migrations yet
            pass  # noqa
