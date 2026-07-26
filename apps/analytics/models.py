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
    notes_created = models.PositiveSmallIntegerField(default=0)
    focus_minutes = models.PositiveIntegerField(default=0)
    prayer_minutes = models.PositiveIntegerField(default=0)
    rules_completed = models.PositiveIntegerField(default=0)
    reminders_completed = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'daily_stats'
        unique_together = ['user', 'date']
        ordering = ['-date']

    def __str__(self):
        return f'{self.user.email}: {self.date}'


class AppUsage(models.Model):
    """Tracks app usage - screen time, sessions, most visited pages."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='app_usage'
    )
    screen_time_seconds = models.PositiveIntegerField(default=0)
    session_count = models.PositiveIntegerField(default=0)
    most_visited_page = models.CharField(max_length=200, blank=True)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'app_usage'
        unique_together = ['user', 'date']
        ordering = ['-date']

    def __str__(self):
        return f'{self.user.email}: {self.date} ({self.screen_time_seconds}s)'
