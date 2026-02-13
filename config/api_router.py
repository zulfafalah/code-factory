from django.conf import settings
from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework.routers import SimpleRouter

from palpal.users.api.views import UserViewSet
from yttoolkit.views import DownloadStartAPIView
from yttoolkit.views import YouTubeMP3ViewSet
from kokorean.views import ManhwaViewSet
from ceritain.views import (
    StoryNarrationCreateAPIView,
    StoryNarrationListAPIView,
    StoryNarrationStatusAPIView,
    StoryNarrationStreamingAPIView,
    StoryNarrationTrendingAPIView,
)

router = DefaultRouter() if settings.DEBUG else SimpleRouter()

router.register("users", UserViewSet)
# Register yttoolkit API endpoints under v1/yttoolkit
router.register("v1/yttoolkit/mp3", YouTubeMP3ViewSet, basename="yttoolkit/mp3")
# Register kokorean API endpoints under v1/kokorean
router.register("v1/kokorean/manhwa", ManhwaViewSet, basename="kokorean/manhwa")

app_name = "api"
urlpatterns = [
    *router.urls,

    # yttoolkit API endpoints
    path(
        "v1/yttoolkit/mp3/start",
        DownloadStartAPIView.as_view(),
        name="v1_start_download",
    ),
    # ceritain API endpoints
    path(
        "v1/ceritain/story-narration/",
        StoryNarrationListAPIView.as_view(),
        name="v1_list_story_narration",
    ),
    path(
        "v1/ceritain/story-narration/create",
        StoryNarrationCreateAPIView.as_view(),
        name="v1_create_story_narration",
    ),
    path(
        "v1/ceritain/story-narration/<int:story_narration_id>/status",
        StoryNarrationStatusAPIView.as_view(),
        name="v1_story_narration_status",
    ),
    path(
        "v1/ceritain/story-narration/<int:story_narration_id>/streaming",
        StoryNarrationStreamingAPIView.as_view(),
        name="v1_story_narration_streaming",
    ),
    path(
        "v1/ceritain/story-narration/trending",
        StoryNarrationTrendingAPIView.as_view(),
        name="v1_story_narration_trending",
    ),
]

