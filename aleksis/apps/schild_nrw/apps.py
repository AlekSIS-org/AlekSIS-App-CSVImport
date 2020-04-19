from aleksis.core.util.apps import AppConfig


class SchILDNRWConfig(AppConfig):
    name = "aleksis.apps.schild_nrw"
    verbose_name = "AlekSIS — SchILD-NRW interface"

    urls = {
        "Repository": "https://edugit.org/AlekSIS/official/AlekSIS-App-SchILD/",
    }
    licence = "EUPL-1.2+"
    copyright = (
        ([2019], "Dominik George", "dominik.george@teckids.org"),
        ([2019], "mirabilos", "thorsten.glaser@teckids.org"),
        ([2019], "Tom Teichler", "tom.teichler@teckids.org"),
    )
