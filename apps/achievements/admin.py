from django.contrib import admin
from .models import Achievement, UserAchievement


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ['code', 'title', 'category', 'trigger_event', 'threshold_value', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['title', 'code', 'description']


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ['user', 'achievement', 'current_progress', 'is_unlocked', 'unlocked_at']
    list_filter = ['is_unlocked']
    search_fields = ['user__email', 'achievement__title']
