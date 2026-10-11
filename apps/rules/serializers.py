from rest_framework import serializers
from .models import Rule, RuleCategory, RuleCompletion


class RuleCategorySerializer(serializers.ModelSerializer):
    rule_count = serializers.ReadOnlyField()

    class Meta:
        model = RuleCategory
        fields = ['id', 'name', 'color', 'icon', 'order', 'rule_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'rule_count', 'created_at', 'updated_at']


class RuleSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    is_completed_today = serializers.ReadOnlyField()
    current_streak = serializers.ReadOnlyField()

    def validate_scriptures(self, value):
        """Keep only well-formed {reference, text} items (max 20, trimmed)."""
        if value in (None, ''):
            return []
        if not isinstance(value, list):
            raise serializers.ValidationError('Scriptures must be a list.')
        cleaned = []
        for item in value[:20]:
            if not isinstance(item, dict):
                raise serializers.ValidationError('Each scripture must be an object.')
            reference = str(item.get('reference') or '').strip()[:200]
            text = str(item.get('text') or '').strip()[:5000]
            if reference or text:
                cleaned.append({'reference': reference, 'text': text})
        return cleaned

    class Meta:
        model = Rule
        fields = [
            'id', 'title', 'description', 'category', 'category_name',
            'color', 'is_pinned', 'is_favorite', 'is_archived',
            'order', 'is_daily', 'scriptures', 'is_completed_today', 'current_streak',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class RuleCompletionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RuleCompletion
        fields = ['id', 'rule', 'completed_date', 'is_completed', 'completed_at', 'note']
        read_only_fields = ['id', 'completed_at']


class RuleReorderSerializer(serializers.Serializer):
    """Payload for POST /rules/reorder/ — an ordered list of rule IDs."""
    ordered_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)


class RuleCategoryReorderSerializer(serializers.Serializer):
    """Payload for POST /rules/categories/reorder/ — an ordered list of category IDs."""
    ordered_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)