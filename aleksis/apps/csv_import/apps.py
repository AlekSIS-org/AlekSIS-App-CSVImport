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
