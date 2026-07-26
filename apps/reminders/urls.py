from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('categories', views.ReminderCategoryViewSet, basename='reminder-category')
router.register('', views.ReminderViewSet, basename='reminder')

urlpatterns = [
    path('', include(router.urls)),
]
