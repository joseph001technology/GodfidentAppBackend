from django.db import models
from django.conf import settings
from django.utils import timezone


class FCMDevice(models.Model):
    """Firebase Cloud Messaging device token for push notifications.

    Only used for the non-essential, backend-stored case (streak/achievement
    notifications) — time-based reminders below are scheduled entirely
    on-device via flutter_local_notifications, since the backend has no way
    to reach a phone that's offline. Push here is a nice-to-have, not load-bearing.
    """
    DEVICE_TYPE_CHOICES = [
        ('android', 'Android'),
        ('ios', 'iOS'),
        ('web', 'Web'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='fcm_devices'
    )
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPE_CHOICES)
    token = models.CharField(max_length=500)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'fcm_devices'
        unique_together = ['user', 'token']

    def __str__(self):
        return f'{self.user.email}: {self.device_type}'


class Notification(models.Model):
    TYPE_CHOICES = [
        ('devotional', 'Daily Devotional'),
        ('reading_reminder', 'Reading Reminder'),
        ('prayer_reminder', 'Prayer Reminder'),
        ('streak', 'Streak Update'),
        ('plan_complete', 'Plan Completed'),
        ('reminder', 'Reminder'),
        ('general', 'General'),
        ('achievement', 'Achievement Unlocked'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.email}: {self.title}'
