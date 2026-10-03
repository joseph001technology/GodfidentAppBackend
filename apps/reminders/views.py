from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db import models
from django.utils import timezone

from .models import Reminder, ReminderCategory, ReminderHistory
from .serializers import ReminderSerializer, ReminderCategorySerializer, ReminderHistorySerializer
from . import services


class ReminderCategoryViewSet(viewsets.ModelViewSet):
    serializer_class = ReminderCategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ReminderCategory.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ReminderViewSet(viewsets.ModelViewSet):
    serializer_class = ReminderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['date', 'time', 'created_at']
    ordering = ['date', 'time']

    def get_queryset(self):
        qs = Reminder.objects.filter(user=self.request.user).select_related('category')

        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        category_id = self.request.query_params.get('category_id')
        if category_id:
            qs = qs.filter(category_id=category_id)

        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            qs = qs.filter(date__gte=start_date)
        if end_date:
            qs = qs.filter(date__lte=end_date)

        overdue = self.request.query_params.get('overdue')
        if overdue == 'true':
            today = timezone.now().date()
            now = timezone.now().time()
            qs = qs.filter(
                models.Q(date__lt=today) | models.Q(date=today, time__lt=now),
                status='pending',
            )

        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        reminder = self.get_object()
        services.complete_reminder(reminder)
        return Response({
            'success': True,
            'message': 'Reminder completed!',
            'data': ReminderSerializer(reminder).data,
        })

    @action(detail=True, methods=['post'])
    def snooze(self, request, pk=None):
        reminder = self.get_object()
        minutes = request.data.get('minutes', 10)
        services.snooze_reminder(reminder, int(minutes))
        return Response({
            'success': True,
            'message': f'Reminder snoozed for {minutes} minutes.',
        })

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        reminder = self.get_object()
        history = reminder.history.all()
        serializer = ReminderHistorySerializer(history, many=True)
        return Response({'success': True, 'data': serializer.data})

    @action(detail=False, methods=['get'])
    def calendar(self, request):
        """Get reminders grouped by date for calendar view."""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if not start_date or not end_date:
            today = timezone.now().date()
            start_date = today.replace(day=1)
            import calendar
            _, last_day = calendar.monthrange(today.year, today.month)
            end_date = today.replace(day=last_day)

        reminders = self.get_queryset().filter(date__gte=start_date, date__lte=end_date)

        from collections import defaultdict
        calendar_data = defaultdict(list)
        for r in reminders:
            calendar_data[str(r.date)].append({
                'id': r.id,
                'title': r.title,
                'time': str(r.time) if r.time else None,
                'status': r.status,
                'category_name': r.category.name if r.category else None,
                'color': r.category.color if r.category else '#E17055',
            })

        return Response({
            'success': True,
            'data': dict(calendar_data),
        })

    @action(detail=False, methods=['get'])
    def stats(self, request):
        reminders = self.get_queryset()
        today = timezone.now().date()
        total = reminders.count()
        completed = reminders.filter(status='completed').count()
        pending = reminders.filter(status='pending', date__gte=today).count()
        overdue = reminders.filter(
            models.Q(date__lt=today) | models.Q(date=today, time__lt=timezone.now().time()),
            status='pending',
        ).count()
        missed = reminders.filter(status='missed').count()

        return Response({
            'success': True,
            'data': {
                'total': total,
                'completed': completed,
                'pending': pending,
                'overdue': overdue,
                'missed': missed,
                'completion_rate': round((completed / total * 100), 1) if total else 0,
            }
        })
