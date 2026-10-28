from rest_framework import serializers

from . import services
from .models import OnlineVideo, OnlineVideoCollection


class OnlineVideoSerializer(serializers.ModelSerializer):
    """What the phone receives."""
    collection = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = OnlineVideo
        fields = ['id', 'url', 'platform', 'dedupe_key', 'collection', 'custom_title', 'created_at']
        read_only_fields = fields


def _owned_collection(request, value):
    if value is None:
        return None
    # Another user's collection is reported exactly like one that does not exist.
    if not OnlineVideoCollection.objects.filter(pk=value.pk, user=request.user).exists():
        raise serializers.ValidationError('Collection not found.')
    return value


class OnlineVideoCreateSerializer(serializers.Serializer):
    id = serializers.UUIDField(required=False)
    url = serializers.CharField(max_length=services.MAX_URL_LENGTH)
    # Accepted but never trusted: the server detects the platform itself.
    platform = serializers.CharField(required=False, allow_blank=True, max_length=20)
    dedupe_key = serializers.CharField(required=False, allow_blank=True, max_length=300)
    collection = serializers.PrimaryKeyRelatedField(
        queryset=OnlineVideoCollection.objects.all(), required=False, allow_null=True
    )
    custom_title = serializers.CharField(required=False, allow_blank=True, max_length=200)

    def validate_url(self, value):
        return services.clean_url(value)

    def validate_collection(self, value):
        return _owned_collection(self.context['request'], value)

    def validate(self, attrs):
        platform = services.detect_platform(attrs['url'])
        attrs['platform'] = platform
        attrs['dedupe_key'] = services.make_dedupe_key(attrs['url'], platform, attrs.get('dedupe_key', ''))
        attrs['custom_title'] = (attrs.get('custom_title') or '').strip()
        return attrs


class OnlineVideoUpdateSerializer(serializers.Serializer):
    collection = serializers.PrimaryKeyRelatedField(
        queryset=OnlineVideoCollection.objects.all(), required=False, allow_null=True
    )
    custom_title = serializers.CharField(required=False, allow_blank=True, max_length=200)

    def validate_collection(self, value):
        return _owned_collection(self.context['request'], value)

    def validate_custom_title(self, value):
        return value.strip()


class CollectionSerializer(serializers.ModelSerializer):
    video_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = OnlineVideoCollection
        fields = ['id', 'name', 'video_count', 'created_at']
        read_only_fields = ['video_count', 'created_at']
        # The phone may choose the id (retry-safe creation); it is checked in the view.
        extra_kwargs = {'id': {'read_only': False, 'required': False}}

    def validate_name(self, value):
        value = (value or '').strip()
        if not value:
            raise serializers.ValidationError('Give the collection a name.')
        return value
