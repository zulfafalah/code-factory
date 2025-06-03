from django.urls import path

from . import views

app_name = "yttoolkit"

urlpatterns = [
    path("", views.download_list, name="download_list"),
    path("start/", views.start_download, name="start_download"),
    path("api/start/", views.api_start_download, name="api_start_download"),
    path(
        "api/status/<int:download_id>/",
        views.api_download_status,
        name="api_download_status",
    ),
    path("download/<int:download_id>/", views.download_file, name="download_file"),
]
