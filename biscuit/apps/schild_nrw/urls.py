from django.urls import path

from . import views


urlpatterns = [
    path('import', views.schild_import, name='schild_import'),
]
