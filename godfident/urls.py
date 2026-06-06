from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('api/', include('apps.api.urls')),


    # API docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # App routes
    path('api/auth/', include('apps.accounts.urls')),
    path('api/bible/', include('apps.bible.urls')),
    path('api/devotionals/', include('apps.devotionals.urls')),
    path('api/reading-plans/', include('apps.reading_plans.urls')),
    path('api/prayer/', include('apps.prayer.urls')),
    path('api/ai/', include('apps.ai_assistant.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
    path('api/analytics/', include('apps.analytics.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
