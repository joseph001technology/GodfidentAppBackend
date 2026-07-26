from django.db import models
from django.conf import settings
from django.utils import timezone


class BlockedApp(models.Model):
    """An app to block during focus sessions (Android integration)."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='blocked_apps'
    )
    app_name = models.CharField(max_length=200)
    package_name = models.CharField(max_length=300)  # Android package name
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'blocked_apps'
        unique_together = ['user', 'package_name']

    def __str__(self):
        return self.app_name


class BlockedWebsite(models.Model):
    """A website to block during focus sessions."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='blocked_websites'
    )
    url = models.URLField(max_length=500)
    domain = models.CharField(max_length=300)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'blocked_websites'
        unique_together = ['user', 'domain']

    def __str__(self):
        return self.domain


class WhitelistApp(models.Model):
    """Apps allowed during focus mode (whitelist approach)."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='whitelist_apps'
    )
    app_name = models.CharField(max_length=200)
    package_name = models.CharField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'whitelist_apps'
        unique_together = ['user', 'package_name']

    def __str__(self):
        return self.app_name


class WhitelistWebsite(models.Model):
    """Websites allowed during focus mode."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='whitelist_websites'
    )
    url = models.URLField(max_length=500)
    domain = models.CharField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'whitelist_websites'
        unique_together = ['user', 'domain']


class FocusSchedule(models.Model):
    """Recurring focus session schedule."""
    DAY_CHOICES = [
        (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'),
        (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='focus_schedules'
    )
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'focus_schedules'
        ordering = ['day_of_week', 'start_time']

    def __str__(self):
        return f'{self.get_day_of_week_display()} {self.start_time}-{self.end_time}'


class FocusSession(models.Model):
    """A single focus session record."""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('interrupted', 'Interrupted'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='focus_sessions'
    )
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    blocked_attempts = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'focus_sessions'
        ordering = ['-started_at']

    def __str__(self):
        return f'Focus {self.started_at.date()} - {self.duration_minutes}min'

    @property
    def time_saved_minutes(self):
        """Calculate estimated time saved by blocking distractions."""
        return self.blocked_attempts * 2  # estimate 2 min per blocked attempt

    def end_session(self, status='completed'):
        self.ended_at = timezone.now()
        self.duration_minutes = int((self.ended_at - self.started_at).total_seconds() / 60)
        self.status = status
        self.save(update_fields=['ended_at', 'duration_minutes', 'status'])


class BlockedAttempt(models.Model):
    """Records a blocked attempt to access a restricted app/website."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='blocked_attempts'
    )
    session = models.ForeignKey(
        FocusSession, on_delete=models.CASCADE, null=True, blank=True, related_name='attempts'
    )
    target_type = models.CharField(max_length=20, choices=[('app', 'App'), ('website', 'Website')])
    target_name = models.CharField(max_length=300)
    attempted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'blocked_attempts'
        ordering = ['-attempted_at']

    def __str__(self):
        return f'Blocked {self.target_type}: {self.target_name}'
