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


class PrayerSession(models.Model):
    """A prayer session with timer tracking."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='prayer_sessions'
    )
    title = models.CharField(max_length=200, blank=True)
    duration_minutes = models.PositiveIntegerField(default=0)
    duration_seconds = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)
    planned_minutes = models.PositiveIntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'prayer_sessions'
        ordering = ['-started_at']

    def __str__(self):
        return f'{self.user.email}: {self.title or "Prayer Session"} ({self.duration_minutes}min)'


class PrayerTimerLog(models.Model):
    """Logs individual timer sessions for analytics."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='prayer_timer_logs'
    )
    duration_seconds = models.PositiveIntegerField()
    started_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'prayer_timer_logs'
        ordering = ['-started_at']

    def __str__(self):
        return f'{self.user.email}: {self.duration_seconds}s'


class PrayerJournal(models.Model):
    """A personal prayer journal entry."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='prayer_journals'
    )
    title = models.CharField(max_length=300)
    content = models.TextField()
    scripture = models.CharField(max_length=200, blank=True)
    mood = models.CharField(max_length=50, blank=True)
    is_private = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'prayer_journals'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.email}: {self.title[:50]}'


class PrayerStreak(models.Model):
    """Tracks a user's prayer streak."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='prayer_streak'
    )
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    last_prayer_date = models.DateField(null=True, blank=True)
    total_days_prayed = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'prayer_streaks'

    def __str__(self):
        return f'{self.user.email}: {self.current_streak} day streak'

    def update_streak(self):
        from django.utils import timezone
        today = timezone.now().date()
        if self.last_prayer_date == today:
            return
        if self.last_prayer_date and (today - self.last_prayer_date).days == 1:
            self.current_streak += 1
        elif self.last_prayer_date and (today - self.last_prayer_date).days > 1:
            self.current_streak = 1
        else:
            self.current_streak = 1
        self.last_prayer_date = today
        self.total_days_prayed += 1
        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak
        self.save()
