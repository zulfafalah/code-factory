from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import YouTubeMP3ViewSet, DownloadStartAPIView, CookieRefreshAPIView

app_name = "yttoolkit"

# Create router for viewsets
router = DefaultRouter()
router.register(r'downloads', YouTubeMP3ViewSet, basename='downloads')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),

    # Additional API endpoints
    path('download/start/', DownloadStartAPIView.as_view(), name='download-start'),
    path('cookies/refresh/', CookieRefreshAPIView.as_view(), name='cookie-refresh'),
]
