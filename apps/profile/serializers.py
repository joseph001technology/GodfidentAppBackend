from rest_framework import serializers
from .models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['reading_streak', 'prayer_streak', 'focus_streak',
                  'total_reading_minutes', 'total_prayer_minutes', 'total_focus_minutes']
        read_only_fields = []