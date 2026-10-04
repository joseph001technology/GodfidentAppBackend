from rest_framework import viewsets, generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.hashers import check_password, make_password
from django.db import IntegrityError
from datetime import timedelta
from django.utils import timezone
from rest_framework.views import APIView

from .models import (
    BlockedApp, BlockedWebsite, WhitelistApp, WhitelistWebsite,
    FocusSchedule, FocusSession, BlockedAttempt, WebsiteProtectionKey,
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
        services.end_session(
            session,
            serializer.validated_data['status'],
            serializer.validated_data.get('duration_minutes'),
        )
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


class BlockedAttemptListView(generics.ListAPIView):
    """List all blocked attempts for the current user."""
    serializer_class = BlockedAttemptSerializer
    permission_classes = [IsAuthenticated]
    ordering = ['-attempted_at']

    def get_queryset(self):
        return BlockedAttempt.objects.filter(user=self.request.user).order_by('-attempted_at')



class WebsiteKeyView(APIView):
    """GET: does this account have a Website Protection Key?  POST: create it (once)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        k = WebsiteProtectionKey.objects.filter(user=request.user).first()
        return Response({'has_key': k is not None, 'locked_seconds': k.locked_seconds() if k else 0})

    def post(self, request):
        key = str(request.data.get('key', ''))
        if len(key) < 4:
            return Response({'key': ['Use at least 4 characters.']}, status=status.HTTP_400_BAD_REQUEST)
        if WebsiteProtectionKey.objects.filter(user=request.user).exists():
            return Response(
                {'detail': 'A Website Protection Key already exists for this account.'},
                status=status.HTTP_409_CONFLICT,
            )
        try:
            WebsiteProtectionKey.objects.create(user=request.user, key_hash=make_password(key))
        except IntegrityError:
            return Response(
                {'detail': 'A Website Protection Key already exists for this account.'},
                status=status.HTTP_409_CONFLICT,
            )
        return Response({'has_key': True}, status=status.HTTP_201_CREATED)


class WebsiteKeyVerifyView(APIView):
    """POST {key}: checks the key, counts wrong attempts and enforces the lockout."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        k = WebsiteProtectionKey.objects.filter(user=request.user).first()
        if k is None:
            return Response({'detail': 'No Website Protection Key has been created yet.'},
                            status=status.HTTP_404_NOT_FOUND)
        locked = k.locked_seconds()
        if locked:
            return Response({'ok': False, 'locked_seconds': locked}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        if check_password(str(request.data.get('key', '')), k.key_hash):
            if k.failed_attempts or k.locked_until:
                k.failed_attempts = 0
                k.locked_until = None
                k.save(update_fields=['failed_attempts', 'locked_until', 'updated_at'])
            return Response({'ok': True})

        k.failed_attempts += 1
        if k.failed_attempts >= WebsiteProtectionKey.MAX_ATTEMPTS:
            k.failed_attempts = 0
            k.locked_until = timezone.now() + timedelta(seconds=WebsiteProtectionKey.LOCK_SECONDS)
        k.save(update_fields=['failed_attempts', 'locked_until', 'updated_at'])
        return Response({
            'ok': False,
            'remaining_attempts': WebsiteProtectionKey.MAX_ATTEMPTS - k.failed_attempts if not k.locked_until else 0,
            'locked_seconds': k.locked_seconds(),
        })
