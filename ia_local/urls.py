from django.urls import path

from . import views

app_name = "ia_local"

urlpatterns = [
    path("", views.consulta_ia, name="consulta"),
    path("consultar/", views.consulta_ia_json, name="consultar"),
]
