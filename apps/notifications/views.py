from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from .models import Notification, FCMDevice
from .serializers import NotificationSerializer, FCMDeviceSerializer
from .permissions import IsNotificationOwner, IsFCMDeviceOwner


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    # Was missing an object-level owner check — IsAuthenticated alone means
    # any logged-in user could read/edit/delete another user's notification
    # by id, the same class of bug already caught once in `rules`.
    permission_classes = [IsAuthenticated, IsNotificationOwner]

    def get_queryset(self):
        qs = Notification.objects.filter(user=self.request.user)
        unread_only = self.request.query_params.get('unread')
        if unread_only == 'true':
            qs = qs.filter(is_read=False)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save(update_fields=['is_read', 'read_at'])
        return Response({'success': True})

    # Note: ModelViewSet already exposes DELETE /notifications/{id}/ (destroy) —
    # this custom action is redundant with that and was removed to avoid two
    # routes doing the same thing. Use the standard DELETE endpoint instead.

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(
            is_read=True, read_at=timezone.now()
        )
        return Response({'success': True, 'message': 'All notifications marked as read.'})

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({'success': True, 'count': count})


class FCMDeviceViewSet(viewsets.ModelViewSet):
    """Manage FCM device tokens for push notifications."""
    serializer_class = FCMDeviceSerializer
    permission_classes = [IsAuthenticated, IsFCMDeviceOwner]

    def get_queryset(self):
        return FCMDevice.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Re-registering an existing token (app reinstall, token refresh) should
        # update it rather than 500 on the unique_together(user, token) clash.
        token = serializer.validated_data.get('token')
        existing = FCMDevice.objects.filter(user=self.request.user, token=token).first()
        if existing:
            for attr, value in serializer.validated_data.items():
                setattr(existing, attr, value)
            existing.is_active = True
            existing.save()
            serializer.instance = existing
        else:
            serializer.save(user=self.request.user)
