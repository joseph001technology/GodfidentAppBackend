from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('categories', views.CategoryViewSet, basename='devotional-category')
router.register('', views.DevotionalViewSet, basename='devotional')

urlpatterns = [
    path('today/', views.TodayDevotionalView.as_view(), name='today-devotional'),
    path('saved/', views.SavedDevotionalsView.as_view(), name='saved-devotionals'),
    path('', include(router.urls)),
]
