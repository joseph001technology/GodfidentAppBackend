from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('categories', views.PrayerCategoryViewSet, basename='prayer-category')
router.register('', views.PrayerViewSet, basename='prayer')
router.register('sessions', views.PrayerSessionViewSet, basename='prayer-session')
router.register('journals', views.PrayerJournalViewSet, basename='prayer-journal')

urlpatterns = [
    path('', include(router.urls)),
    path('streak/', views.PrayerStreakView.as_view(), name='prayer-streak'),
]
