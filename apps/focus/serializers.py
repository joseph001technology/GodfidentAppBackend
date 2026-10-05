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
    class Meta:
        model = FocusSchedule
        fields = [
            'id', 'title', 'purpose', 'days', 'once_date', 'start_time', 'end_time',
            'duration_minutes', 'ringtone', 'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'end_time', 'created_at']

    def validate_days(self, value):
        if not isinstance(value, list) or any(not isinstance(d, int) or d < 1 or d > 7 for d in value):
            raise serializers.ValidationError('Days must be a list of numbers from 1 (Mon) to 7 (Sun).')
        return sorted(set(value))

    def validate_duration_minutes(self, value):
        if value < 1 or value > 720:
            raise serializers.ValidationError('Choose between 1 minute and 12 hours.')
        return value


class FocusSessionSerializer(serializers.ModelSerializer):
    time_saved_minutes = serializers.ReadOnlyField()

    class Meta:
        model = FocusSession
        fields = [
            'id', 'started_at', 'ended_at', 'duration_minutes',
            'status', 'blocked_attempts', 'time_saved_minutes', 'purpose',
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
    # The phone knows the planned length; used so a session that ended while the
    # app was closed is not recorded as lasting until the app was next opened.
    duration_minutes = serializers.IntegerField(required=False, min_value=0, max_value=1440)


class LogBlockedAttemptSerializer(serializers.Serializer):
    target_type = serializers.ChoiceField(choices=['app', 'website'])
    target_name = serializers.CharField(max_length=300)
    session_id = serializers.IntegerField(required=False, allow_null=True)
