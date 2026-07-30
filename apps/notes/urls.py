from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('folders', views.FolderViewSet, basename='note-folder')
router.register('topics', views.TopicViewSet, basename='note-topic')
router.register('', views.NoteViewSet, basename='note')

urlpatterns = [
    path('', include(router.urls)),
]