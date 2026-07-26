from rest_framework import serializers
from .models import (
    BlockedApp, BlockedWebsite, WhitelistApp, WhitelistWebsite,
    FocusSchedule, FocusSession, BlockedAttempt,
)


class BlockedAppSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlockedApp
        fields = ['id', 'app_name', 'package_name', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class BlockedWebsiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlockedWebsite
        fields = ['id', 'url', 'domain', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class WhitelistAppSerializer(serializers.ModelSerializer):
    class Meta:
        model = WhitelistApp
        fields = ['id', 'app_name', 'package_name', 'created_at']
        read_only_fields = ['id', 'created_at']


class WhitelistWebsiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = WhitelistWebsite
        fields = ['id', 'url', 'domain', 'created_at']
        read_only_fields = ['id', 'created_at']


class FocusScheduleSerializer(serializers.ModelSerializer):
    day_name = serializers.SerializerMethodField()

    class Meta:
        model = FocusSchedule
        fields = ['id', 'day_of_week', 'day_name', 'start_time', 'end_time', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_day_name(self, obj):
        return obj.get_day_of_week_display()


class FocusSessionSerializer(serializers.ModelSerializer):
    time_saved_minutes = serializers.ReadOnlyField()

    class Meta:
        model = FocusSession
        fields = [
            'id', 'started_at', 'ended_at', 'duration_minutes',
            'status', 'blocked_attempts', 'time_saved_minutes',
        ]
        read_only_fields = ['id', 'started_at']


class BlockedAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlockedAttempt
        fields = ['id', 'session', 'target_type', 'target_name', 'attempted_at']
        read_only_fields = ['id', 'attempted_at']


class StartFocusSerializer(serializers.Serializer):
    """Serializer for starting a focus session."""
    pass


class EndFocusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['completed', 'interrupted', 'cancelled'], default='completed')


class LogBlockedAttemptSerializer(serializers.Serializer):
    target_type = serializers.ChoiceField(choices=['app', 'website'])
    target_name = serializers.CharField(max_length=300)
    session_id = serializers.IntegerField(required=False, allow_null=True)
