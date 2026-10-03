from rest_framework import serializers
from .models import Reminder, ReminderCategory, ReminderHistory


class ReminderCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ReminderCategory
        fields = ['id', 'name', 'color', 'icon', 'created_at']
        read_only_fields = ['id', 'created_at']


class ReminderSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    is_overdue = serializers.ReadOnlyField()
    is_completed = serializers.SerializerMethodField()

    def get_is_completed(self, obj):
        return obj.status == 'completed'

    class Meta:
        model = Reminder
        fields = [
            'id', 'title', 'description', 'category', 'category_name',
            'date', 'time', 'repeat', 'repeat_frequency', 'repeat_until',
            'status', 'is_snoozed', 'snooze_until',
            'next_occurrence', 'bible_reference',
            'is_overdue', 'is_completed',
            'is_enabled', 'is_alarm', 'snooze_minutes', 'target_page',
            'created_at', 'updated_at', 'completed_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'completed_at']


class ReminderHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ReminderHistory
        fields = ['id', 'reminder', 'action', 'timestamp', 'note']
        read_only_fields = ['id', 'timestamp']
