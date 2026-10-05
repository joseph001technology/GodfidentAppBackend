from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('categories', views.PrayerCategoryViewSet, basename='prayer-category')
router.register('sessions', views.PrayerSessionViewSet, basename='prayer-session')
router.register('journals', views.PrayerJournalViewSet, basename='prayer-journal')
router.register('logs', views.PrayerLogViewSet, basename='prayer-log')
router.register('timer-logs', views.PrayerTimerLogViewSet, basename='prayer-timer-log')
# Registered LAST: an empty prefix has a catch-all detail route (<pk>/) that would
# otherwise swallow /sessions/, /journals/, /logs/ ...
router.register('', views.PrayerViewSet, basename='prayer')

urlpatterns = [
    path('streak/', views.PrayerStreakView.as_view(), name='prayer-streak'),
    path('', include(router.urls)),
]
