from django.contrib import admin
from django.urls import path
from django.urls import include

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("admin/", admin.site.urls),
    path("ia/", include("ia_local.urls")),
]
