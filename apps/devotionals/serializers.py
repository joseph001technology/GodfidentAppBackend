from rest_framework import serializers
from .models import DevotionalCategory, Devotional, DailyDevotional, SavedDevotional, DevotionalReadHistory
from django.utils import timezone


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = DevotionalCategory
        fields = ['id', 'name', 'description', 'icon']


class DevotionalSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    is_saved = serializers.SerializerMethodField()
    is_read = serializers.SerializerMethodField()

    class Meta:
        model = Devotional
        fields = [
            'id', 'title', 'scripture_reference', 'scripture_text',
            'reflection', 'prayer', 'application', 'key_takeaway',
            'author', 'category', 'category_name', 'publish_date',
            'is_saved', 'is_read', 'created_at',
        ]

    def get_is_saved(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return SavedDevotional.objects.filter(user=request.user, devotional=obj).exists()
        return False

    def get_is_read(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return DevotionalReadHistory.objects.filter(user=request.user, devotional=obj).exists()
        return False


class DailyDevotionalSerializer(serializers.ModelSerializer):
    devotional = DevotionalSerializer(read_only=True)

    class Meta:
        model = DailyDevotional
        fields = ['date', 'devotional']
