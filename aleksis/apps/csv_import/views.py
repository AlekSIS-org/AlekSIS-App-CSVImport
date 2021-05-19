import os

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext as _

from rules.contrib.views import permission_required

from aleksis.core.util.celery_progress import render_progress_page
from aleksis.core.util.core_helpers import handle_uploaded_file, path_and_rename

from .forms import CSVUploadForm
from .util.process import import_csv


@permission_required("csv_import.import_data_rule")
def csv_import(request: HttpRequest) -> HttpResponse:
    context = {}

    upload_form = CSVUploadForm()

    if request.method == "POST":
        upload_form = CSVUploadForm(request.POST, request.FILES)

        if upload_form.is_valid():
            filename = os.path.join(
                settings.MEDIA_ROOT,
                path_and_rename(None, request.FILES["csv"].name, upload_to="tmp"),
            )
            handle_uploaded_file(request.FILES["csv"], filename)

            result = import_csv.delay(
                upload_form.cleaned_data["template"].pk,
                filename,
                school_term=upload_form.cleaned_data["school_term"].pk,
            )

            return render_progress_page(
                request,
                result,
                title=_("Progress: Import data from CSV"),
                progress_title=_("Import objects …"),
                success_message=_("The import was done successfully."),
                error_message=_("There was a problem while importing data."),
                back_url=reverse("csv_import"),
            )

    context["upload_form"] = upload_form

    return render(request, "csv_import/csv_import.html", context)
