from rest_framework import viewsets, generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from django.utils import timezone

from .models import DevotionalCategory, Devotional, DailyDevotional, SavedDevotional, DevotionalReadHistory
from .serializers import CategorySerializer, DevotionalSerializer, DailyDevotionalSerializer


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DevotionalCategory.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]


class DevotionalViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DevotionalSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['category']
    search_fields = ['title', 'scripture_reference', 'reflection']

    def get_queryset(self):
        return Devotional.objects.filter(is_published=True).select_related('category')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Mark as read
        DevotionalReadHistory.objects.get_or_create(user=request.user, devotional=instance)
        serializer = self.get_serializer(instance)
        return Response({'success': True, 'data': serializer.data})

    @action(detail=True, methods=['post'])
    def save(self, request, pk=None):
        devotional = self.get_object()
        _, created = SavedDevotional.objects.get_or_create(user=request.user, devotional=devotional)
        return Response({
            'success': True,
            'message': 'Devotional saved.' if created else 'Already saved.',
        })

    @action(detail=True, methods=['delete'])
    def unsave(self, request, pk=None):
        devotional = self.get_object()
        SavedDevotional.objects.filter(user=request.user, devotional=devotional).delete()
        return Response({'success': True, 'message': 'Removed from saved.'})


class TodayDevotionalView(generics.RetrieveAPIView):
    """GET /devotionals/today/ - get today's devotional"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        try:
            daily = DailyDevotional.objects.select_related('devotional__category').get(date=today)
            serializer = DailyDevotionalSerializer(daily, context={'request': request})
            return Response({'success': True, 'data': serializer.data})
        except DailyDevotional.DoesNotExist:
            # Fall back to latest devotional if none scheduled
            devotional = Devotional.objects.filter(is_published=True).order_by('-created_at').first()
            if devotional:
                DevotionalReadHistory.objects.get_or_create(user=request.user, devotional=devotional)
                return Response({'success': True, 'data': DevotionalSerializer(devotional, context={'request': request}).data})
            return Response({'success': False, 'message': 'No devotional available for today.'}, status=404)


class SavedDevotionalsView(generics.ListAPIView):
    """GET /devotionals/saved/ - list user's saved devotionals"""
    serializer_class = DevotionalSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Devotional.objects.filter(
            saves__user=self.request.user
        ).select_related('category').order_by('-saves__saved_at')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
