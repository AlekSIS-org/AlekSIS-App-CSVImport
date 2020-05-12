from django.urls import path

from . import views

urlpatterns = [
    path("import", views.csv_import, name="csv_import"),
]
