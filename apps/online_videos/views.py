import uuid

from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from . import services
from .models import OnlineVideo, OnlineVideoCollection
from .serializers import (
    CollectionSerializer, OnlineVideoCreateSerializer, OnlineVideoSerializer, OnlineVideoUpdateSerializer,
)


class VideoPagination(LimitOffsetPagination):
    """?limit=24&offset=0 -> {count, next, previous, results}. The phone asks for one page at a time."""
    default_limit = 24
    max_limit = 100


class OnlineVideoViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """The signed-in user's saved online-video links.

    GET    /videos/?limit=&offset=&collection=<uuid>|none   one page, newest first
    POST   /videos/                                         save a link (idempotent per user)
    GET    /videos/<id>/
    PATCH  /videos/<id>/   {collection?, custom_title?}
    DELETE /videos/<id>/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = OnlineVideoSerializer
    pagination_class = VideoPagination
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        # Every query starts from the caller's own rows: other users' records do not exist for them.
        qs = OnlineVideo.objects.filter(user=self.request.user)
        if self.action == 'list':
            coll = self.request.query_params.get('collection')
            if coll == 'none':
                qs = qs.filter(collection__isnull=True)
            elif coll:
                try:
                    qs = qs.filter(collection_id=uuid.UUID(coll))
                except ValueError:
                    raise ValidationError({'collection': 'Not a valid collection id.'})
        return qs

    def create(self, request, *args, **kwargs):
        ser = OnlineVideoCreateSerializer(data=request.data, context={'request': request})
        ser.is_valid(raise_exception=True)
        d = ser.validated_data

        existing = OnlineVideo.objects.filter(user=request.user, dedupe_key=d['dedupe_key']).first()
        if existing is not None:
            return Response({**OnlineVideoSerializer(existing).data, 'duplicate': True})

        if OnlineVideo.objects.filter(user=request.user).count() >= services.MAX_VIDEOS_PER_USER:
            raise ValidationError({'detail': 'Your online video library is full. Remove some links first.'})

        values = dict(
            user=request.user, url=d['url'], platform=d['platform'], dedupe_key=d['dedupe_key'],
            collection=d.get('collection'), custom_title=d['custom_title'],
        )
        # Use the phone's id only if nobody has it (a taken id is never revealed or reused).
        wanted = d.get('id')
        if wanted and not OnlineVideo.objects.filter(pk=wanted).exists():
            values['id'] = wanted
        try:
            with transaction.atomic():
                obj = OnlineVideo.objects.create(**values)
        except IntegrityError:
            # Two requests saved the same video at the same moment: report the winner.
            winner = OnlineVideo.objects.filter(user=request.user, dedupe_key=d['dedupe_key']).first()
            if winner is None:
                raise
            return Response({**OnlineVideoSerializer(winner).data, 'duplicate': True})
        return Response({**OnlineVideoSerializer(obj).data, 'duplicate': False}, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        obj = self.get_object()
        ser = OnlineVideoUpdateSerializer(data=request.data, partial=True, context={'request': request})
        ser.is_valid(raise_exception=True)
        fields = []
        for name in ('collection', 'custom_title'):
            if name in ser.validated_data:
                setattr(obj, name, ser.validated_data[name])
                fields.append(name)
        if fields:
            obj.save(update_fields=fields + ['updated_at'])
        return Response(OnlineVideoSerializer(obj).data)


class CollectionViewSet(
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """The signed-in user's collections. Deleting one never deletes its videos."""
    permission_classes = [IsAuthenticated]
    serializer_class = CollectionSerializer
    pagination_class = None  # at most MAX_COLLECTIONS_PER_USER, shown together
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        return (
            OnlineVideoCollection.objects.filter(user=self.request.user)
            .annotate(video_count=Count('videos'))
        )

    def list(self, request, *args, **kwargs):
        rows = CollectionSerializer(self.get_queryset(), many=True).data
        mine = OnlineVideo.objects.filter(user=request.user)
        # One query for both numbers the filter chips need.
        totals = mine.aggregate(total=Count('id'), unsorted=Count('id', filter=Q(collection__isnull=True)))
        return Response({
            'results': rows,
            'total_videos': totals['total'],
            'unsorted_videos': totals['unsorted'],
        })

    def create(self, request, *args, **kwargs):
        ser = CollectionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        name = ser.validated_data['name'][:60]
        existing = OnlineVideoCollection.objects.filter(user=request.user, name_key=name.lower()).first()
        if existing is not None:
            existing.video_count = existing.videos.count()
            return Response(CollectionSerializer(existing).data)  # same name = same collection
        if OnlineVideoCollection.objects.filter(user=request.user).count() >= services.MAX_COLLECTIONS_PER_USER:
            raise ValidationError({'detail': 'You have reached the limit of collections.'})
        values = {'user': request.user, 'name': name}
        wanted = ser.validated_data.get('id')
        if wanted and not OnlineVideoCollection.objects.filter(pk=wanted).exists():
            values['id'] = wanted
        try:
            with transaction.atomic():
                obj = OnlineVideoCollection.objects.create(**values)
        except IntegrityError:
            obj = OnlineVideoCollection.objects.get(user=request.user, name_key=name.lower())
        obj.video_count = 0
        return Response(CollectionSerializer(obj).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        obj = self.get_object()
        ser = CollectionSerializer(obj, data={'name': request.data.get('name', '')}, partial=False)
        ser.is_valid(raise_exception=True)
        name = ser.validated_data['name'][:60]
        clash = (
            OnlineVideoCollection.objects.filter(user=request.user, name_key=name.lower())
            .exclude(pk=obj.pk).exists()
        )
        if clash:
            return Response({'detail': 'You already have a collection with that name.'}, status=status.HTTP_409_CONFLICT)
        obj.name = name
        try:
            with transaction.atomic():
                obj.save(update_fields=['name', 'updated_at'])
        except IntegrityError:
            return Response({'detail': 'You already have a collection with that name.'}, status=status.HTTP_409_CONFLICT)
        obj.video_count = obj.videos.count()
        return Response(CollectionSerializer(obj).data)
