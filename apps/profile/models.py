from django.db import models
from django.conf import settings


class Profile(models.Model):
    """Extended profile statistics (one-to-one with User)."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile_stats')

    # Streaks
    reading_streak = models.PositiveIntegerField(default=0)
    prayer_streak = models.PositiveIntegerField(default=0)
    focus_streak = models.PositiveIntegerField(default=0)

    # Totals
    total_reading_minutes = models.PositiveIntegerField(default=0)
    total_prayer_minutes = models.PositiveIntegerField(default=0)
    total_focus_minutes = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'profile_stats'

    def __str__(self):
        return f'Profile: {self.user.email}'
