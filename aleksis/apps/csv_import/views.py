from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from rules.contrib.views import permission_required

from .forms import CSVUploadForm
from .util.process import import_csv


@permission_required("csv_import.import_data")
def csv_import(request: HttpRequest) -> HttpResponse:
    context = {}

    upload_form = CSVUploadForm()

    if request.method == "POST":
        upload_form = CSVUploadForm(request.POST, request.FILES)

        if upload_form.is_valid():
            import_csv(
                request,
                upload_form.cleaned_data["template"],
                request.FILES["csv"],
            )

    context["upload_form"] = upload_form

    return render(request, "csv_import/csv_import.html", context)
