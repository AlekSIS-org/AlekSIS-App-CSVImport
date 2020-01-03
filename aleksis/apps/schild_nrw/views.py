from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from aleksis.core.decorators import admin_required

from .forms import SchILDNRWUploadForm
from .util import schild_import_csv


@login_required
@admin_required
def schild_import(request: HttpRequest) -> HttpResponse:
    context = {}

    upload_form = SchILDNRWUploadForm()

    if request.method == "POST":
        upload_form = SchILDNRWUploadForm(request.POST, request.FILES)

        if upload_form.is_valid():
            schild_import_csv(
                request,
                request.FILES["teachers_csv"],
                request.FILES["students_csv"],
                request.FILES["guardians_csv"],
            )

    context["upload_form"] = upload_form

    return render(request, "schild_nrw/schild_import.html", context)
