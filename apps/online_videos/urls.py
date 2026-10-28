from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('videos', views.OnlineVideoViewSet, basename='online-video')
router.register('collections', views.CollectionViewSet, basename='online-video-collection')

urlpatterns = [
    path('', include(router.urls)),
]
