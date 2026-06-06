from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('plans', views.ReadingPlanViewSet, basename='reading-plan')
router.register('my-plans', views.UserReadingPlanViewSet, basename='user-reading-plan')

urlpatterns = [
    path('streak/', views.ReadingStreakView.as_view(), name='reading-streak'),
    path('', include(router.urls)),
]
