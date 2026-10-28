import uuid

from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel


class OnlineVideoCollection(TimeStampedModel):
    """A folder the user made to organise saved online videos. Owned by one user."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='online_video_collections'
    )
    name = models.CharField(max_length=60)
    # Lower-cased copy of the name, so "Sermons" and "sermons" count as the same collection
    # on every database (a plain unique constraint is case-sensitive on PostgreSQL).
    name_key = models.CharField(max_length=60, editable=False)

    class Meta:
        db_table = 'online_video_collections'
        ordering = ['name_key']
        constraints = [
            models.UniqueConstraint(fields=['user', 'name_key'], name='uniq_ovcoll_user_name'),
        ]

    def save(self, *args, **kwargs):
        self.name = (self.name or '').strip()
        self.name_key = self.name.lower()
        update_fields = kwargs.get('update_fields')
        if update_fields is not None and 'name' in update_fields:
            kwargs['update_fields'] = list(set(update_fields) | {'name_key'})
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class OnlineVideo(TimeStampedModel):
    """A saved LINK to a video hosted by another platform. No video data is stored here.

    Titles and thumbnails are deliberately not stored: the phone looks them up again from the
    platform when needed (they are regenerable). `custom_title` is the one exception, because
    a name the user typed cannot be regenerated.
    """
    PLATFORM_CHOICES = [
        ('youtube', 'YouTube'), ('instagram', 'Instagram'), ('tiktok', 'TikTok'),
        ('facebook', 'Facebook'), ('vimeo', 'Vimeo'), ('other', 'Other'),
    ]

    # The phone may choose the id when saving (so a retried request cannot create a second row).
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='online_videos'
    )
    url = models.URLField(max_length=2000)
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, default='other')
    dedupe_key = models.CharField(max_length=300)
    collection = models.ForeignKey(
        OnlineVideoCollection, null=True, blank=True, on_delete=models.SET_NULL, related_name='videos'
    )
    custom_title = models.CharField(max_length=200, blank=True, default='')

    class Meta:
        db_table = 'online_videos'
        ordering = ['-created_at', '-id']
        constraints = [
            # The same video once per user (never across users: each library is private).
            models.UniqueConstraint(fields=['user', 'dedupe_key'], name='uniq_onlinevideo_user_key'),
        ]
        indexes = [
            models.Index(fields=['user', '-created_at', '-id'], name='ov_user_created_idx'),
            models.Index(fields=['user', 'collection', '-created_at'], name='ov_user_coll_idx'),
        ]

    def __str__(self):
        return f'{self.platform}: {self.url[:60]}'
