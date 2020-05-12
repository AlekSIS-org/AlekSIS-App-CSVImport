from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from rules.contrib.views import permission_required

from .forms import CSVUploadForm
from .util.process import schild_import_csv


@permission_required("csv_import.import_data")
def csv_import(request: HttpRequest) -> HttpResponse:
    context = {}

    upload_form = CSVUploadForm()

    if request.method == "POST":
        upload_form = CSVUploadForm(request.POST, request.FILES)

        if upload_form.is_valid():
            schild_import_csv(
                request,
                request.FILES["teachers_csv"],
                request.FILES["students_csv"],
                request.FILES["guardians_csv"],
            )

    context["upload_form"] = upload_form

    return render(request, "csv_import/csv_import.html", context)
