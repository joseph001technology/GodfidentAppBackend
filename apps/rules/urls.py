from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('categories', views.RuleCategoryViewSet, basename='rule-category')
router.register('', views.RuleViewSet, basename='rule')

urlpatterns = [
    path('', include(router.urls)),
]
