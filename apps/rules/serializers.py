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

    class Meta:
        model = Rule
        fields = [
            'id', 'title', 'description', 'category', 'category_name',
            'color', 'is_pinned', 'is_favorite', 'is_archived',
            'order', 'is_daily', 'is_completed_today', 'current_streak',
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