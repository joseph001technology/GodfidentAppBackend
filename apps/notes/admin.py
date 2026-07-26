from django.contrib import admin
from .models import Note, Folder, Topic


@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'color', 'order', 'note_count']
    search_fields = ['name', 'user__email']
    list_filter = ['user']


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'color']
    search_fields = ['name', 'user__email']


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'folder', 'is_pinned', 'is_favorite', 'is_archived', 'updated_at']
    list_filter = ['is_pinned', 'is_favorite', 'is_archived', 'user']
    search_fields = ['title', 'content', 'user__email']
    raw_id_fields = ['user', 'folder']
    filter_horizontal = ['topics']
