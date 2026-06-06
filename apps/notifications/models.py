from django.db import models
from django.conf import settings


class Notification(models.Model):
    TYPE_CHOICES = [
        ('devotional', 'Daily Devotional'),
        ('reading_reminder', 'Reading Reminder'),
        ('prayer_reminder', 'Prayer Reminder'),
        ('streak', 'Streak Update'),
        ('plan_complete', 'Plan Completed'),
        ('general', 'General'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    data = models.JSONField(default=dict)  # extra payload (e.g. link to devotional)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.email}: {self.title}'
