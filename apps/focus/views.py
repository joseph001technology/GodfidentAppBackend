from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from .models import (
    BlockedApp, BlockedWebsite, WhitelistApp, WhitelistWebsite,
    FocusSchedule, FocusSession, BlockedAttempt,
)
from .serializers import (
    BlockedAppSerializer, BlockedWebsiteSerializer,
    WhitelistAppSerializer, WhitelistWebsiteSerializer,
    FocusScheduleSerializer, FocusSessionSerializer,
    BlockedAttemptSerializer, StartFocusSerializer, EndFocusSerializer,
    LogBlockedAttemptSerializer,
)
from . import services


class BlockedAppViewSet(viewsets.ModelViewSet):
    serializer_class = BlockedAppSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return BlockedApp.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class BlockedWebsiteViewSet(viewsets.ModelViewSet):
    serializer_class = BlockedWebsiteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return BlockedWebsite.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class WhitelistAppViewSet(viewsets.ModelViewSet):
    serializer_class = WhitelistAppSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return WhitelistApp.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class WhitelistWebsiteViewSet(viewsets.ModelViewSet):
    serializer_class = WhitelistWebsiteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return WhitelistWebsite.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class FocusScheduleViewSet(viewsets.ModelViewSet):
    serializer_class = FocusScheduleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FocusSchedule.objects.filter(user=self.request.user).order_by('day_of_week', 'start_time')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class FocusSessionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = FocusSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = FocusSession.objects.filter(user=self.request.user)
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs.order_by('-started_at')

    @action(detail=False, methods=['post'])
    def start(self, request):
        session = services.start_session(request.user)
        return Response({
            'success': True,
            'message': 'Focus session started!',
            'data': FocusSessionSerializer(session).data,
        })

    @action(detail=True, methods=['post'])
    def end(self, request, pk=None):
        session = self.get_object()
        serializer = EndFocusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.end_session(session, serializer.validated_data['status'])
        return Response({
            'success': True,
            'message': 'Focus session ended.',
            'data': FocusSessionSerializer(session).data,
        })

    @action(detail=False, methods=['post'])
    def log_attempt(self, request):
        serializer = LogBlockedAttemptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        session_id = serializer.validated_data.get('session_id')
        session = None
        if session_id:
            try:
                session = FocusSession.objects.get(id=session_id, user=request.user, status='active')
            except FocusSession.DoesNotExist:
                pass

        attempt = services.log_blocked_attempt(
            user=request.user,
            target_type=serializer.validated_data['target_type'],
            target_name=serializer.validated_data['target_name'],
            session=session,
        )
        return Response({
            'success': True,
            'data': BlockedAttemptSerializer(attempt).data,
        })

    @action(detail=False, methods=['get'])
    def stats(self, request):
        stats = services.get_focus_stats(request.user)
        return Response({'success': True, 'data': stats})

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get the currently active session if any."""
        session = FocusSession.objects.filter(
            user=request.user, status='active'
        ).first()
        if session:
            return Response({
                'success': True,
                'data': FocusSessionSerializer(session).data,
            })
        return Response({'success': True, 'data': None})
