from django.db import models
from django.conf import settings
from django.utils import timezone


class DevotionalCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)  # icon name for frontend

    class Meta:
        db_table = 'devotional_categories'
        verbose_name_plural = 'Devotional Categories'

    def __str__(self):
        return self.name


class Devotional(models.Model):
    """A devotional entry with scripture, reflection, and prayer."""
    category = models.ForeignKey(
        DevotionalCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='devotionals'
    )
    title = models.CharField(max_length=200)
    scripture_reference = models.CharField(max_length=100)  # e.g. "John 3:16-17"
    scripture_text = models.TextField()
    reflection = models.TextField()
    prayer = models.TextField()
    application = models.TextField(blank=True)
    key_takeaway = models.CharField(max_length=500, blank=True)
    author = models.CharField(max_length=100, blank=True, default='Godfident')
    is_published = models.BooleanField(default=True)
    publish_date = models.DateField(null=True, blank=True)  # for scheduled devotionals
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'devotionals'
        ordering = ['-publish_date', '-created_at']

    def __str__(self):
        return self.title


class DailyDevotional(models.Model):
    """Assigns a devotional to a calendar date."""
    date = models.DateField(unique=True)
    devotional = models.ForeignKey(Devotional, on_delete=models.CASCADE, related_name='daily_assignments')

    class Meta:
        db_table = 'daily_devotionals'
        ordering = ['-date']

    def __str__(self):
        return f'{self.date}: {self.devotional.title}'


class SavedDevotional(models.Model):
    """User saves a devotional for later."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_devotionals')
    devotional = models.ForeignKey(Devotional, on_delete=models.CASCADE, related_name='saves')
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'saved_devotionals'
        unique_together = ['user', 'devotional']
        ordering = ['-saved_at']

    def __str__(self):
        return f'{self.user.email} saved: {self.devotional.title}'


class DevotionalReadHistory(models.Model):
    """Tracks which devotionals a user has read."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='devotional_history')
    devotional = models.ForeignKey(Devotional, on_delete=models.CASCADE)
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'devotional_read_history'
        unique_together = ['user', 'devotional']
        ordering = ['-read_at']
