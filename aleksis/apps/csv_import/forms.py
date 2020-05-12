from django import forms
from django.utils.translation import gettext_lazy as _


class CSVUploadForm(forms.Form):
    teachers_csv = forms.FileField(label=_("CSV export of teachers"))
    students_csv = forms.FileField(label=_("CSV export of students"))
    guardians_csv = forms.FileField(label=_("CSV export of guardians/parents"))
