from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ManhwaViewSet

# Router untuk ViewSet
router = DefaultRouter()
router.register(r'manhwa', ManhwaViewSet, basename='manhwa')

app_name = 'kokorean'

urlpatterns = [
    path('', include(router.urls)),
]
