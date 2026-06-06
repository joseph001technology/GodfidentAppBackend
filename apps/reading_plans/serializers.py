from rest_framework import serializers
from .models import ReadingPlan, ReadingPlanDay, UserReadingPlan, DayProgress, ReadingStreak


class ReadingPlanDaySerializer(serializers.ModelSerializer):
    class Meta:
        model = ReadingPlanDay
        fields = ['id', 'day_number', 'title', 'readings']


class ReadingPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReadingPlan
        fields = ['id', 'name', 'description', 'plan_type', 'duration_days']


class UserReadingPlanSerializer(serializers.ModelSerializer):
    plan = ReadingPlanSerializer(read_only=True)
    plan_id = serializers.PrimaryKeyRelatedField(
        queryset=ReadingPlan.objects.all(), source='plan', write_only=True
    )
    progress_percent = serializers.ReadOnlyField()
    current_day_detail = serializers.SerializerMethodField()

    class Meta:
        model = UserReadingPlan
        fields = [
            'id', 'plan', 'plan_id', 'status', 'started_at',
            'completed_at', 'current_day', 'progress_percent', 'current_day_detail',
        ]
        read_only_fields = ['id', 'started_at', 'completed_at', 'current_day']

    def get_current_day_detail(self, obj):
        try:
            day = obj.plan.days.get(day_number=obj.current_day)
            return ReadingPlanDaySerializer(day).data
        except ReadingPlanDay.DoesNotExist:
            return None


class DayProgressSerializer(serializers.ModelSerializer):
    day_number = serializers.IntegerField(source='plan_day.day_number', read_only=True)
    title = serializers.CharField(source='plan_day.title', read_only=True)

    class Meta:
        model = DayProgress
        fields = ['id', 'day_number', 'title', 'is_completed', 'completed_at']


class ReadingStreakSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReadingStreak
        fields = ['current_streak', 'longest_streak', 'last_read_date', 'total_days_read']
