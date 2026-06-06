from django.db import models
from django.conf import settings


class PrayerCategory(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        db_table = 'prayer_categories'
        verbose_name_plural = 'Prayer Categories'

    def __str__(self):
        return self.name


class Prayer(models.Model):
    """A prayer request or praise report."""
    TYPE_CHOICES = [
        ('request', 'Prayer Request'),
        ('praise', 'Praise Report'),
        ('intercession', 'Intercession'),
        ('thanksgiving', 'Thanksgiving'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('answered', 'Answered'),
        ('archived', 'Archived'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='prayers')
    category = models.ForeignKey(
        PrayerCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='prayers'
    )
    prayer_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='request')
    title = models.CharField(max_length=200)
    content = models.TextField()
    scripture = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    answered_note = models.TextField(blank=True)
    is_private = models.BooleanField(default=True)
    reminder_enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    answered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'prayers'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.email}: {self.title}'


class PrayerLog(models.Model):
    """Track when user prays for a prayer item."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='prayer_logs')
    prayer = models.ForeignKey(Prayer, on_delete=models.CASCADE, related_name='logs')
    note = models.TextField(blank=True)
    prayed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'prayer_logs'
        ordering = ['-prayed_at']

    def __str__(self):
        return f'{self.user.email} prayed: {self.prayer.title}'
