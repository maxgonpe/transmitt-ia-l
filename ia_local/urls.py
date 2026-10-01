from django.urls import path

from . import views

app_name = "ia_local"

urlpatterns = [
    path("", views.consulta_ia, name="consulta"),
    path("consultar/", views.consulta_ia_json, name="consultar"),
    path("test/",views.index_test,name="index_test"),
    path("test-json/",views.consulta_test_json,name="test_json"),
    path("diagnostico-documentos/", views.diagnostico_documentos, name="diagnostico_documentos", ),
    path("test-guardar-regla/", views.guardar_regla_test_json, name="guardar_regla_test_json",),
    path("test-guardar-patron/", views.guardar_patron_test_json, name="guardar_patron_test_json",),
    path("reglas/", views.reglas_semanticas, name="reglas_semanticas",),
    path("reglas/<int:pk>/estado/", views.cambiar_estado_regla, name="cambiar_estado_regla",),
]
