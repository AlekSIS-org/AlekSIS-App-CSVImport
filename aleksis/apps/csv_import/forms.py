from django import forms
from django.utils.translation import gettext_lazy as _

from aleksis.apps.csv_import.models import ImportTemplate


class CSVUploadForm(forms.Form):
    csv = forms.FileField(label=_("CSV file"))
    template = forms.ModelChoiceField(
        queryset=ImportTemplate.objects.all(), label=_("Import template")
    )
