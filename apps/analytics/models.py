from django.db import models
from django.conf import settings


class ReadingActivity(models.Model):
    """Records each reading event for analytics."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reading_activities')
    book_name = models.CharField(max_length=50)
    chapter = models.PositiveSmallIntegerField()
    translation = models.CharField(max_length=10, default='KJV')
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reading_activities'
        ordering = ['-read_at']
        indexes = [
            models.Index(fields=['user', 'read_at']),
        ]

    def __str__(self):
        return f'{self.user.email}: {self.book_name} {self.chapter} @ {self.read_at.date()}'


class DailyStats(models.Model):
    """Aggregated daily stats per user (computed/cached)."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='daily_stats')
    date = models.DateField()
    chapters_read = models.PositiveSmallIntegerField(default=0)
    prayers_logged = models.PositiveSmallIntegerField(default=0)
    devotionals_read = models.PositiveSmallIntegerField(default=0)
    ai_interactions = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = 'daily_stats'
        unique_together = ['user', 'date']
        ordering = ['-date']

    def __str__(self):
        return f'{self.user.email}: {self.date}'
