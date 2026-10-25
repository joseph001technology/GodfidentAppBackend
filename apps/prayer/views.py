from datetime import timedelta
from rest_framework import viewsets, generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone

from .models import PrayerCategory, Prayer, PrayerLog, PrayerSession, PrayerTimerLog, PrayerJournal, PrayerStreak
from .serializers import PrayerCategorySerializer, PrayerSerializer, PrayerLogSerializer, PrayerSessionSerializer, PrayerTimerLogSerializer, PrayerJournalSerializer, PrayerStreakSerializer


class PrayerCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PrayerCategory.objects.all()
    serializer_class = PrayerCategorySerializer
    permission_classes = [IsAuthenticated]


class PrayerViewSet(viewsets.ModelViewSet):
    serializer_class = PrayerSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['prayer_type', 'status', 'category']
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'updated_at']

    def get_queryset(self):
        return Prayer.objects.filter(user=self.request.user).select_related('category')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_answered(self, request, pk=None):
        prayer = self.get_object()
        prayer.status = 'answered'
        # An answered prayer is kept as a thanksgiving prayer.
        prayer.prayer_type = 'thanksgiving'
        prayer.answered_at = timezone.now()
        prayer.answered_note = request.data.get('note', '') or ''
        prayer.save(update_fields=['status', 'prayer_type', 'answered_at', 'answered_note'])
        return Response({
            'success': True,
            'message': 'Prayer marked as answered! Praise God!',
            'data': PrayerSerializer(prayer).data,
        })

    @action(detail=True, methods=['post'])
    def log_prayer(self, request, pk=None):
        prayer = self.get_object()
        log = PrayerLog.objects.create(
            user=request.user,
            prayer=prayer,
            note=request.data.get('note', ''),
        )
        streak, _ = PrayerStreak.objects.get_or_create(user=request.user)
        streak.update_streak()
        return Response({
            'success': True,
            'message': 'Prayer logged.',
            'data': PrayerLogSerializer(log).data,
        })

    @action(detail=False, methods=['get'])
    def stats(self, request):
        prayers = self.get_queryset()
        return Response({
            'success': True,
            'data': {
                'total': prayers.count(),
                'active': prayers.filter(status='active').count(),
                'answered': prayers.filter(status='answered').count(),
                'by_type': {
                    'requests': prayers.filter(prayer_type='request').count(),
                    'praises': prayers.filter(prayer_type='praise').count(),
                    'intercessions': prayers.filter(prayer_type='intercession').count(),
                    'thanksgiving': prayers.filter(prayer_type='thanksgiving').count(),
                },
                'times_prayed': PrayerLog.objects.filter(user=request.user).count(),
            }
        })


class PrayerLogViewSet(viewsets.ModelViewSet):
    """Dedicated endpoint for prayer logs."""
    serializer_class = PrayerLogSerializer
    permission_classes = [IsAuthenticated]
    ordering = ['-prayed_at']

    def get_queryset(self):
        return PrayerLog.objects.filter(user=self.request.user).select_related('prayer')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PrayerTimerLogViewSet(viewsets.ModelViewSet):
    """Prayer timer logs for analytics."""
    serializer_class = PrayerTimerLogSerializer
    permission_classes = [IsAuthenticated]
    ordering = ['-started_at']

    def get_queryset(self):
        return PrayerTimerLog.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PrayerStreakView(generics.RetrieveAPIView):
    serializer_class = PrayerStreakSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        streak, _ = PrayerStreak.objects.get_or_create(user=request.user)
        return Response({'success': True, 'data': PrayerStreakSerializer(streak).data})


class PrayerSessionViewSet(viewsets.ModelViewSet):
    """Manage prayer sessions with timer tracking."""
    serializer_class = PrayerSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PrayerSession.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def end(self, request, pk=None):
        session = self.get_object()
        try:
            duration = max(0, int(request.data.get('duration_seconds', 0) or 0))
        except (TypeError, ValueError):
            duration = 0
        if session.is_completed:  # ending twice must not count the day twice
            return Response({'success': True, 'message': 'Prayer session already ended.',
                             'data': PrayerSessionSerializer(session).data})
        session.duration_seconds = duration
        session.duration_minutes = duration // 60
        session.is_completed = True
        session.ended_at = timezone.now()
        session.save(update_fields=['duration_seconds', 'duration_minutes', 'is_completed', 'ended_at'])

        # The day counts on which the session STARTED, in the person's own time zone
        # (a 11 pm session that ends at 1 am belongs to the start day).
        try:
            off = max(-14 * 60, min(14 * 60, int(request.data.get('tz_offset', 0) or 0)))
        except (TypeError, ValueError):
            off = 0
        start_day = (session.started_at + timedelta(minutes=off)).date()

        log = PrayerTimerLog.objects.create(user=request.user, duration_seconds=duration)
        PrayerTimerLog.objects.filter(pk=log.pk).update(started_at=session.started_at)

        streak, _ = PrayerStreak.objects.get_or_create(user=request.user)
        streak.update_streak(day=start_day)

        return Response({
            'success': True,
            'message': 'Prayer session ended.',
            'data': PrayerSessionSerializer(session).data,
        })


class PrayerJournalViewSet(viewsets.ModelViewSet):
    """Manage personal prayer journal entries."""
    serializer_class = PrayerJournalSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return PrayerJournal.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

