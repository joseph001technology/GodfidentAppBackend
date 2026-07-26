from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.management import call_command

from .models import Achievement, UserAchievement
from .serializers import AchievementSerializer, UserAchievementSerializer
from . import services


class AchievementViewSet(viewsets.ReadOnlyModelViewSet):
    """View all available achievements."""
    queryset = Achievement.objects.filter(is_active=True)
    serializer_class = AchievementSerializer
    permission_classes = [IsAuthenticated]


class UserAchievementViewSet(viewsets.ReadOnlyModelViewSet):
    """View the current user's achievements and progress."""
    serializer_class = UserAchievementSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserAchievement.objects.filter(
            user=self.request.user
        ).select_related('achievement').order_by('-is_unlocked', '-unlocked_at')

    @action(detail=False, methods=['get'])
    def summary(self, request):
        summary = services.get_user_achievements_summary(request.user)
        return Response({'success': True, 'data': summary})

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get most recently unlocked achievements."""
        recent = self.get_queryset().filter(is_unlocked=True)[:5]
        serializer = self.get_serializer(recent, many=True)
        return Response({'success': True, 'data': serializer.data})

    @action(detail=False, methods=['post'])
    def seed(self, request):
        """Seed achievements (admin only)."""
        if not request.user.is_staff:
            return Response({'success': False, 'message': 'Admin only.'}, status=403)
        count = services.seed_achievements()
        return Response({'success': True, 'message': f'{count} achievements seeded.'})
