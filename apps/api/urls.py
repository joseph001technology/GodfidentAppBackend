from django.urls import path, include
from apps.common.health import health
from .views import ApiRootView, GlobalSearchView

urlpatterns = [
    path('', ApiRootView.as_view(), name='api-root'),
    path('health/', health, name='api-health'),
    path('search/', GlobalSearchView.as_view(), name='global-search'),
]
