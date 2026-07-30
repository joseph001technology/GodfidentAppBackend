from rest_framework import serializers
from .models import Note, Folder, Topic, NoteVersion, RuleCategory, Rule


# ---------------------------------------------------------------------------
# General notes
# ---------------------------------------------------------------------------

class FolderSerializer(serializers.ModelSerializer):
    note_count = serializers.ReadOnlyField()

    class Meta:
        model = Folder
        fields = ['id', 'name', 'color', 'icon', 'parent', 'order', 'note_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ['id', 'name', 'color', 'created_at']
        read_only_fields = ['id', 'created_at']


class NoteListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""
    folder_name = serializers.CharField(source='folder.name', read_only=True)
    topics_list = TopicSerializer(source='topics', many=True, read_only=True)

    class Meta:
        model = Note
        fields = [
            'id', 'title', 'folder', 'folder_name', 'topics_list',
            'is_pinned', 'is_favorite', 'is_archived',
            'bible_references', 'version',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'version']


class NoteDetailSerializer(serializers.ModelSerializer):
    """Full serializer for detail/retrieve views."""
    folder_name = serializers.CharField(source='folder.name', read_only=True)
    topics_list = TopicSerializer(source='topics', many=True, read_only=True)
    topic_ids = serializers.PrimaryKeyRelatedField(
        source='topics', queryset=Topic.objects.all(), many=True, write_only=True, required=False
    )

    class Meta:
        model = Note
        fields = [
            'id', 'title', 'content', 'folder', 'folder_name',
            'topics', 'topics_list', 'topic_ids',
            'bible_references', 'is_pinned', 'is_favorite', 'is_archived',
            'version', 'created_at', 'updated_at', 'archived_at',
        ]
        read_only_fields = ['id', 'version', 'created_at', 'updated_at', 'archived_at']


class NoteVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = NoteVersion
        fields = ['id', 'version', 'title', 'content', 'created_at']
        read_only_fields = ['id', 'created_at']


class NoteActionSerializer(serializers.Serializer):
    """Serializer for simple action requests (archive, restore, etc.)."""
    pass


# ---------------------------------------------------------------------------
# Universal Rules
# ---------------------------------------------------------------------------

class RuleCategorySerializer(serializers.ModelSerializer):
    rule_count = serializers.ReadOnlyField()

    class Meta:
        model = RuleCategory
        fields = ['id', 'name', 'color', 'icon', 'order', 'rule_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'rule_count', 'created_at', 'updated_at']


class RuleSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Rule
        fields = [
            'id', 'content', 'category', 'category_name', 'order',
            'is_archived', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class RuleReorderSerializer(serializers.Serializer):
    """Payload for POST /rules/reorder/ — an ordered list of rule IDs."""
    ordered_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)


class RuleCategoryReorderSerializer(serializers.Serializer):
    """Payload for POST /rule-categories/reorder/ — an ordered list of category IDs."""
    ordered_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)