from rest_framework import serializers
from .models import PrayerCategory, Prayer, PrayerLog, PrayerSession, PrayerTimerLog, PrayerJournal, PrayerStreak


class PrayerCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PrayerCategory
        fields = ['id', 'name']


class PrayerSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    times_prayed = serializers.SerializerMethodField()

    class Meta:
        model = Prayer
        fields = [
            'id', 'prayer_type', 'title', 'content', 'scripture',
            'status', 'answered_note', 'is_private', 'reminder_enabled',
            'category', 'category_name', 'times_prayed',
            'created_at', 'updated_at', 'answered_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'answered_at']

    def get_times_prayed(self, obj):
        return obj.logs.count()


class PrayerLogSerializer(serializers.ModelSerializer):
    prayer_title = serializers.CharField(source='prayer.title', read_only=True)

    class Meta:
        model = PrayerLog
        fields = ['id', 'prayer', 'prayer_title', 'note', 'prayed_at']
        read_only_fields = ['id', 'prayed_at']


class PrayerSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrayerSession
        fields = ['id', 'title', 'duration_minutes', 'duration_seconds', 'notes',
                  'is_completed', 'started_at', 'ended_at', 'created_at']
        read_only_fields = ['id', 'started_at', 'created_at']


class PrayerTimerLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrayerTimerLog
        fields = ['id', 'duration_seconds', 'started_at']
        read_only_fields = ['id', 'started_at']


class PrayerJournalSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrayerJournal
        fields = ['id', 'title', 'content', 'scripture', 'mood', 'is_private',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class PrayerStreakSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrayerStreak
        fields = ['current_streak', 'longest_streak', 'last_prayer_date', 'total_days_prayed']
