from django.db import models
from django.conf import settings
from django.utils import timezone


class ReadingPlan(models.Model):
    """A structured Bible reading plan."""
    PLAN_TYPES = [
        ('chronological', 'Chronological'),
        ('canonical', 'Canonical (Book by Book)'),
        ('thematic', 'Thematic'),
        ('gospel', 'Gospels Focus'),
        ('nt', 'New Testament'),
        ('ot', 'Old Testament'),
        ('proverbs', 'Proverbs'),
        ('psalms', 'Psalms'),
        ('custom', 'Custom'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField()
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES)
    duration_days = models.PositiveSmallIntegerField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reading_plans'
        ordering = ['duration_days']

    def __str__(self):
        return self.name


class ReadingPlanDay(models.Model):
    """A single day's reading assignment in a plan."""
    plan = models.ForeignKey(ReadingPlan, on_delete=models.CASCADE, related_name='days')
    day_number = models.PositiveSmallIntegerField()  # 1-365
    title = models.CharField(max_length=200, blank=True)
    readings = models.JSONField(default=list)
    # readings format: [{"book": "Genesis", "chapter_start": 1, "chapter_end": 3}, ...]

    class Meta:
        db_table = 'reading_plan_days'
        unique_together = ['plan', 'day_number']
        ordering = ['day_number']

    def __str__(self):
        return f'{self.plan.name} - Day {self.day_number}'


class UserReadingPlan(models.Model):
    """A user's enrollment in a reading plan."""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reading_plans')
    plan = models.ForeignKey(ReadingPlan, on_delete=models.CASCADE, related_name='enrollments')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    current_day = models.PositiveSmallIntegerField(default=1)

    class Meta:
        db_table = 'user_reading_plans'
        unique_together = ['user', 'plan']
        ordering = ['-started_at']

    def __str__(self):
        return f'{self.user.email} - {self.plan.name} ({self.status})'

    @property
    def progress_percent(self):
        if self.plan.duration_days == 0:
            return 0
        completed = self.day_progress.filter(is_completed=True).count()
        return round((completed / self.plan.duration_days) * 100, 1)


class DayProgress(models.Model):
    """Tracks completion of individual plan days."""
    user_plan = models.ForeignKey(UserReadingPlan, on_delete=models.CASCADE, related_name='day_progress')
    plan_day = models.ForeignKey(ReadingPlanDay, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'day_progress'
        unique_together = ['user_plan', 'plan_day']

    def mark_complete(self):
        self.is_completed = True
        self.completed_at = timezone.now()
        self.save(update_fields=['is_completed', 'completed_at'])


class ReadingStreak(models.Model):
    """Tracks a user's reading streak."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reading_streak')
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    last_read_date = models.DateField(null=True, blank=True)
    total_days_read = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'reading_streaks'

    def __str__(self):
        return f'{self.user.email}: {self.current_streak} day streak'

    def update_streak(self):
        today = timezone.now().date()
        if self.last_read_date == today:
            return  # Already counted today
        if self.last_read_date and (today - self.last_read_date).days == 1:
            self.current_streak += 1
        elif self.last_read_date and (today - self.last_read_date).days > 1:
            self.current_streak = 1
        else:
            self.current_streak = 1
        self.last_read_date = today
        self.total_days_read += 1
        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak
        self.save()
