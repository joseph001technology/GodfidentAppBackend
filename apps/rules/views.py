from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from .models import Rule, RuleCategory, RuleCompletion
from .serializers import RuleSerializer, RuleCategorySerializer, RuleCompletionSerializer
from . import services


class RuleCategoryViewSet(viewsets.ModelViewSet):
    serializer_class = RuleCategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return RuleCategory.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class RuleViewSet(viewsets.ModelViewSet):
    serializer_class = RuleSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['order', 'created_at', 'updated_at', 'title']
    ordering = ['order', 'title']

    def get_queryset(self):
        qs = Rule.objects.filter(user=self.request.user).select_related('category')

        is_archived = self.request.query_params.get('archived')
        if is_archived == 'true':
            qs = qs.filter(is_archived=True)
        else:
            qs = qs.filter(is_archived=False)

        category_id = self.request.query_params.get('category_id')
        if category_id:
            qs = qs.filter(category_id=category_id)

        is_pinned = self.request.query_params.get('pinned')
        if is_pinned == 'true':
            qs = qs.filter(is_pinned=True)

        is_favorite = self.request.query_params.get('favorite')
        if is_favorite == 'true':
            qs = qs.filter(is_favorite=True)

        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def toggle_today(self, request, pk=None):
        rule = self.get_object()
        is_completed, message = services.toggle_today_completion(rule)
        return Response({
            'success': True,
            'message': message,
            'is_completed': is_completed,
        })

    @action(detail=True, methods=['post'])
    def toggle_pin(self, request, pk=None):
        rule = self.get_object()
        rule.is_pinned = not rule.is_pinned
        rule.save(update_fields=['is_pinned'])
        return Response({'success': True, 'is_pinned': rule.is_pinned})

    @action(detail=True, methods=['post'])
    def toggle_favorite(self, request, pk=None):
        rule = self.get_object()
        rule.is_favorite = not rule.is_favorite
        rule.save(update_fields=['is_favorite'])
        return Response({'success': True, 'is_favorite': rule.is_favorite})

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        rule = self.get_object()
        rule.is_archived = True
        rule.save(update_fields=['is_archived'])
        return Response({'success': True, 'message': 'Rule archived.'})

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        rule = self.get_object()
        rule.is_archived = False
        rule.save(update_fields=['is_archived'])
        return Response({'success': True, 'message': 'Rule restored.'})

    @action(detail=True, methods=['post'])
    def reorder(self, request, pk=None):
        rule = self.get_object()
        new_order = request.data.get('order')
        if new_order is not None:
            rule.order = new_order
            rule.save(update_fields=['order'])
        return Response({'success': True, 'order': rule.order})

    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get all rules with today's completion status."""
        rules = self.get_queryset().filter(is_archived=False)
        today = timezone.now().date()

        # Annotate with today's completion
        data = []
        for rule in rules:
            completion = RuleCompletion.objects.filter(
                rule=rule, completed_date=today
            ).first()
            rule_data = RuleSerializer(rule, context={'request': request}).data
            rule_data['completed_today'] = completion.is_completed if completion else False
            data.append(rule_data)

        return Response({'success': True, 'data': data})

    @action(detail=False, methods=['get'])
    def stats(self, request):
        rules = self.get_queryset()
        today = timezone.now().date()
        total = rules.count()
        completed_today = RuleCompletion.objects.filter(
            rule__in=rules, completed_date=today, is_completed=True
        ).count()
        return Response({
            'success': True,
            'data': {
                'total': total,
                'completed_today': completed_today,
                'completion_rate': round((completed_today / total * 100), 1) if total else 0,
                'pinned': rules.filter(is_pinned=True).count(),
                'favorites': rules.filter(is_favorite=True).count(),
            }
        })
