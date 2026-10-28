from django.contrib import admin

from .models import OnlineVideo, OnlineVideoCollection


@admin.register(OnlineVideoCollection)
class OnlineVideoCollectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'created_at')
    search_fields = ('name', 'user__email')
    raw_id_fields = ('user',)


@admin.register(OnlineVideo)
class OnlineVideoAdmin(admin.ModelAdmin):
    list_display = ('platform', 'url', 'user', 'collection', 'created_at')
    list_filter = ('platform',)
    search_fields = ('url', 'user__email')
    raw_id_fields = ('user', 'collection')
