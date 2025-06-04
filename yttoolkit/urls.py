from django.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "yttoolkit"

# DRF Router for ViewSets
router = DefaultRouter()
router.register(r"downloads", views.YouTubeMP3ViewSet, basename="downloads")

urlpatterns = [
    # Traditional Django views for web interface
    path("", views.download_list, name="download_list"),
    path("start/", views.start_download, name="start_download"),
    path("download/<int:download_id>/", views.download_file, name="download_file"),
    # DRF API endpoints
    path("api/v1/", include(router.urls)),
    path(
        "api/v1/start/",
        views.DownloadStartAPIView.as_view(),
        name="api_v1_start_download",
    ),
    # Legacy API endpoints for backward compatibility
    path("api/start/", views.api_start_download, name="api_start_download"),
    path(
        "api/status/<int:download_id>/",
        views.api_download_status,
        name="api_download_status",
    ),
    path(
        "api/v1/status/<int:download_id>/",
        views.LegacyDownloadStatusAPIView.as_view(),
        name="api_v1_download_status",
    ),
]
