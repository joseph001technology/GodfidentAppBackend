from django.contrib import admin
from .models import ReadingActivity, DailyStats, AppUsage


@admin.register(ReadingActivity)
class ReadingActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'book_name', 'chapter', 'translation', 'read_at']
    list_filter = ['translation']
    search_fields = ['user__email', 'book_name']


@admin.register(DailyStats)
class DailyStatsAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'chapters_read', 'prayers_logged', 'devotionals_read']
    list_filter = ['date']
    search_fields = ['user__email']


@admin.register(AppUsage)
class AppUsageAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'screen_time_seconds', 'session_count']
    list_filter = ['date']
    search_fields = ['user__email']