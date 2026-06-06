from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('categories', views.PrayerCategoryViewSet, basename='prayer-category')
router.register('', views.PrayerViewSet, basename='prayer')

urlpatterns = [path('', include(router.urls))]
