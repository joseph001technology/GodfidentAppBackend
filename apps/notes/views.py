from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Note, Folder, Topic, RuleCategory, Rule
from .serializers import (
    NoteListSerializer, NoteDetailSerializer,
    FolderSerializer, TopicSerializer, NoteVersionSerializer,
    RuleCategorySerializer, RuleSerializer,
    RuleReorderSerializer, RuleCategoryReorderSerializer,
)
from .permissions import IsOwner
from . import services


# ---------------------------------------------------------------------------
# General notes
# ---------------------------------------------------------------------------

class FolderViewSet(viewsets.ModelViewSet):
    """Manage note folders."""
    serializer_class = FolderSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        return Folder.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TopicViewSet(viewsets.ModelViewSet):
    """Manage note topics/tags."""
    serializer_class = TopicSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        return Topic.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class NoteViewSet(viewsets.ModelViewSet):
    """Manage personal notes with rich text, folders, and topics."""
    permission_classes = [IsAuthenticated, IsOwner]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'updated_at', 'title', 'is_pinned']
    ordering = ['-is_pinned', '-updated_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return NoteListSerializer
        return NoteDetailSerializer

    def get_queryset(self):
        qs = Note.objects.filter(user=self.request.user)
        qs = qs.select_related('folder').prefetch_related('topics')

        # Filter by archive status
        archived = self.request.query_params.get('archived')
        if archived == 'true':
            qs = qs.filter(is_archived=True)
        elif archived == 'false' or archived is None:
            qs = qs.filter(is_archived=False)

        # Filter by favorite
        favorite = self.request.query_params.get('favorite')
        if favorite == 'true':
            qs = qs.filter(is_favorite=True)

        # Filter by folder
        folder_id = self.request.query_params.get('folder_id')
        if folder_id:
            qs = qs.filter(folder_id=folder_id)

        # Filter by topic
        topic_id = self.request.query_params.get('topic_id')
        if topic_id:
            qs = qs.filter(topics__id=topic_id)

        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        note = self.get_object()
        if note.content != serializer.validated_data.get('content', note.content):
            services.create_note_version(note)
        serializer.save()

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        note = self.get_object()
        services.archive_note(note)
        return Response({'success': True, 'message': 'Note archived.'})

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        note = self.get_object()
        services.restore_note(note)
        return Response({'success': True, 'message': 'Note restored.'})

    @action(detail=True, methods=['post'])
    def toggle_pin(self, request, pk=None):
        note = self.get_object()
        note.is_pinned = not note.is_pinned
        note.save(update_fields=['is_pinned'])
        return Response({'success': True, 'is_pinned': note.is_pinned})

    @action(detail=True, methods=['post'])
    def toggle_favorite(self, request, pk=None):
        note = self.get_object()
        note.is_favorite = not note.is_favorite
        note.save(update_fields=['is_favorite'])
        return Response({'success': True, 'is_favorite': note.is_favorite})

    @action(detail=True, methods=['get'])
    def versions(self, request, pk=None):
        note = self.get_object()
        versions = note.versions.all()
        serializer = NoteVersionSerializer(versions, many=True)
        return Response({'success': True, 'data': serializer.data})

    @action(detail=False, methods=['get'])
    def stats(self, request):
        notes = self.get_queryset()
        return Response({
            'success': True,
            'data': {
                'total': notes.count(),
                'favorites': notes.filter(is_favorite=True).count(),
                'archived': Note.objects.filter(user=request.user, is_archived=True).count(),
                'pinned': notes.filter(is_pinned=True).count(),
                'folders': Folder.objects.filter(user=request.user).count(),
                'topics': Topic.objects.filter(user=request.user).count(),
            }
        })


# ---------------------------------------------------------------------------
# Universal Rules
# ---------------------------------------------------------------------------

class RuleCategoryViewSet(viewsets.ModelViewSet):
    """Manage user-created categories for Universal Rules."""
    serializer_class = RuleCategorySerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        return RuleCategory.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'])
    def reorder(self, request):
        """POST /rule-categories/reorder/  body: {"ordered_ids": [3, 1, 2]}"""
        serializer = RuleCategoryReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.reorder_rule_categories(request.user, serializer.validated_data['ordered_ids'])
        return Response({'success': True, 'message': 'Categories reordered.'})


class RuleViewSet(viewsets.ModelViewSet):
    """Manage Universal Rules — short, always-accessible personal principles."""
    serializer_class = RuleSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['category', 'is_archived']
    search_fields = ['content']

    def get_queryset(self):
        qs = Rule.objects.filter(user=self.request.user).select_related('category')

        archived = self.request.query_params.get('archived')
        if archived == 'true':
            qs = qs.filter(is_archived=True)
        elif archived == 'false' or archived is None:
            qs = qs.filter(is_archived=False)

        category_id = self.request.query_params.get('category_id')
        if category_id:
            qs = qs.filter(category_id=category_id)

        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'])
    def reorder(self, request):
        """POST /rules/reorder/  body: {"ordered_ids": [5, 2, 9, 1]}"""
        serializer = RuleReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.reorder_rules(request.user, serializer.validated_data['ordered_ids'])
        return Response({'success': True, 'message': 'Rules reordered.'})

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