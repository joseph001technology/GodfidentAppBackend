from rest_framework import serializers
from .models import ReadingActivity, DailyStats, AppUsage


class ReadingActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ReadingActivity
        fields = ['id', 'book_name', 'chapter', 'translation', 'read_at']
        read_only_fields = ['id', 'read_at']


class DailyStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyStats
        fields = ['id', 'date', 'chapters_read', 'prayers_logged', 'devotionals_read',
                  'ai_interactions', 'notes_created', 'focus_minutes', 'prayer_minutes',
                  'rules_completed', 'reminders_completed']
        read_only_fields = ['id']


class AppUsageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppUsage
        fields = ['id', 'screen_time_seconds', 'session_count', 'most_visited_page', 'date']
        read_only_fields = ['id', 'date']