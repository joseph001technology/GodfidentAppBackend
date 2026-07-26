from django.urls import path, include
from .views import ApiRootView, GlobalSearchView

urlpatterns = [
    path('', ApiRootView.as_view(), name='api-root'),
    path('search/', GlobalSearchView.as_view(), name='global-search'),
]
