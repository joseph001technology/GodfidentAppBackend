from rest_framework import viewsets, generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from .models import ReadingPlan, ReadingPlanDay, UserReadingPlan, DayProgress, ReadingStreak
from .serializers import (
    ReadingPlanSerializer, ReadingPlanDaySerializer,
    UserReadingPlanSerializer, DayProgressSerializer, ReadingStreakSerializer,
)


class ReadingPlanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ReadingPlan.objects.filter(is_active=True)
    serializer_class = ReadingPlanSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['get'])
    def days(self, request, pk=None):
        plan = self.get_object()
        days = plan.days.all()
        return Response({'success': True, 'data': ReadingPlanDaySerializer(days, many=True).data})


class UserReadingPlanViewSet(viewsets.ModelViewSet):
    serializer_class = UserReadingPlanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserReadingPlan.objects.filter(
            user=self.request.user
        ).select_related('plan').prefetch_related('day_progress')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        plan_id = request.data.get('plan_id')
        if UserReadingPlan.objects.filter(user=request.user, plan_id=plan_id, status='active').exists():
            return Response(
                {'success': False, 'message': 'You are already enrolled in this plan.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().create(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def complete_day(self, request, pk=None):
        user_plan = self.get_object()
        day_number = request.data.get('day_number', user_plan.current_day)

        try:
            plan_day = user_plan.plan.days.get(day_number=day_number)
        except ReadingPlanDay.DoesNotExist:
            return Response({'success': False, 'message': 'Day not found.'}, status=404)

        day_progress, _ = DayProgress.objects.get_or_create(
            user_plan=user_plan, plan_day=plan_day
        )
        if not day_progress.is_completed:
            day_progress.mark_complete()
            # Advance current day
            if day_number == user_plan.current_day:
                user_plan.current_day = min(day_number + 1, user_plan.plan.duration_days)
                user_plan.save(update_fields=['current_day'])
            # Check if plan complete
            total = user_plan.plan.duration_days
            completed = user_plan.day_progress.filter(is_completed=True).count()
            if completed >= total:
                user_plan.status = 'completed'
                user_plan.completed_at = timezone.now()
                user_plan.save(update_fields=['status', 'completed_at'])

        # Update reading streak
        streak, _ = ReadingStreak.objects.get_or_create(user=request.user)
        streak.update_streak()

        return Response({'success': True, 'message': f'Day {day_number} marked complete!'})

    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        user_plan = self.get_object()
        user_plan.status = 'paused'
        user_plan.save(update_fields=['status'])
        return Response({'success': True, 'message': 'Plan paused.'})

    @action(detail=True, methods=['post'])
    def resume(self, request, pk=None):
        user_plan = self.get_object()
        user_plan.status = 'active'
        user_plan.save(update_fields=['status'])
        return Response({'success': True, 'message': 'Plan resumed.'})


class ReadingStreakView(generics.RetrieveAPIView):
    serializer_class = ReadingStreakSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        streak, _ = ReadingStreak.objects.get_or_create(user=request.user)
        return Response({'success': True, 'data': ReadingStreakSerializer(streak).data})
