from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from aleksis.apps.csv_import.models import ImportTemplate
from aleksis.core.models import SchoolTerm


class CSVUploadForm(forms.Form):
    csv = forms.FileField(label=_("CSV file"))
    school_term = forms.ModelChoiceField(
        queryset=SchoolTerm.objects.all(), label=_("Related school term"),
    )
    template = forms.ModelChoiceField(
        queryset=ImportTemplate.objects.all(), label=_("Import template")
    )

    def __init__(self, *args, **kwargs):
        try:
            school_terms = SchoolTerm.objects.on_day(timezone.now().date())
            kwargs["initial"] = {
                "school_term": school_terms[0] if school_terms.exists() else None
            }
        except SchoolTerm.DoesNotExist:
            pass
        super().__init__(*args, **kwargs)
