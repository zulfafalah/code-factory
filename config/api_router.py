from django.conf import settings
from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework.routers import SimpleRouter

from palpal.users.api.views import UserViewSet
from yttoolkit.views import DownloadStartAPIView
from yttoolkit.views import YouTubeMP3ViewSet

router = DefaultRouter() if settings.DEBUG else SimpleRouter()

router.register("users", UserViewSet)
# Register yttoolkit API endpoints under v1/yttoolkit
router.register("v1/yttoolkit/mp3", YouTubeMP3ViewSet, basename="yttoolkit/mp3")

app_name = "api"
urlpatterns = [
    *router.urls,

    # yttoolkit API endpoints
    path(
        "v1/yttoolkit/mp3/start",
        DownloadStartAPIView.as_view(),
        name="v1_start_download",
    ),
]
