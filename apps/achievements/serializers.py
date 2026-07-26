from rest_framework import serializers
from .models import Achievement, UserAchievement


class AchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Achievement
        fields = ['id', 'code', 'title', 'description', 'category', 'icon',
                  'criteria_description', 'threshold_value', 'order']
        read_only_fields = ['id']


class UserAchievementSerializer(serializers.ModelSerializer):
    achievement = AchievementSerializer(read_only=True)
    progress_percent = serializers.ReadOnlyField()

    class Meta:
        model = UserAchievement
        fields = ['id', 'achievement', 'current_progress', 'progress_percent',
                  'is_unlocked', 'unlocked_at', 'progress_metadata']
        read_only_fields = ['id', 'unlocked_at']
