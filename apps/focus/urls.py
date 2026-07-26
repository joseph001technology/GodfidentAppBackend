from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('blocked-apps', views.BlockedAppViewSet, basename='blocked-app')
router.register('blocked-websites', views.BlockedWebsiteViewSet, basename='blocked-website')
router.register('whitelist-apps', views.WhitelistAppViewSet, basename='whitelist-app')
router.register('whitelist-websites', views.WhitelistWebsiteViewSet, basename='whitelist-website')
router.register('schedules', views.FocusScheduleViewSet, basename='focus-schedule')
router.register('sessions', views.FocusSessionViewSet, basename='focus-session')

urlpatterns = [
    path('', include(router.urls)),
    path('blocked-attempts/', views.BlockedAttemptListView.as_view(), name='blocked-attempts'),
]
