from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone

from .models import PrayerCategory, Prayer, PrayerLog
from .serializers import PrayerCategorySerializer, PrayerSerializer, PrayerLogSerializer


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
        prayer.answered_at = timezone.now()
        prayer.answered_note = request.data.get('note', '')
        prayer.save(update_fields=['status', 'answered_at', 'answered_note'])
        return Response({'success': True, 'message': 'Prayer marked as answered! Praise God!'})

    @action(detail=True, methods=['post'])
    def log_prayer(self, request, pk=None):
        prayer = self.get_object()
        log = PrayerLog.objects.create(
            user=request.user,
            prayer=prayer,
            note=request.data.get('note', ''),
        )
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
