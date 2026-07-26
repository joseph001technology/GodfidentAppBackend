from django.db import models
from django.conf import settings


class Achievement(models.Model):
    """A predefined achievement that users can unlock."""
    CATEGORY_CHOICES = [
        ('prayer', 'Prayer'),
        ('reading', 'Bible Reading'),
        ('notes', 'Notes'),
        ('streak', 'Streaks'),
        ('focus', 'Focus'),
        ('milestone', 'Milestones'),
        ('devotional', 'Devotionals'),
    ]

    code = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    icon = models.CharField(max_length=100, blank=True)
    criteria_description = models.CharField(max_length=300)

    # What triggers this achievement (for evaluation logic)
    trigger_event = models.CharField(max_length=100, blank=True)
    threshold_value = models.PositiveIntegerField(default=1)

    # Order in display
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'achievements'
        ordering = ['category', 'order']

    def __str__(self):
        return self.title


class UserAchievement(models.Model):
    """Tracks a user's progress towards and unlocking of an achievement."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='achievements'
    )
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE, related_name='user_achievements')
    current_progress = models.PositiveIntegerField(default=0)
    is_unlocked = models.BooleanField(default=False)
    unlocked_at = models.DateTimeField(null=True, blank=True)
    progress_metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'user_achievements'
        unique_together = ['user', 'achievement']
        ordering = ['-is_unlocked', '-unlocked_at']

    def __str__(self):
        return f'{self.user.email}: {self.achievement.title}'

    @property
    def progress_percent(self):
        if self.achievement.threshold_value == 0:
            return 100 if self.is_unlocked else 0
        return min(round((self.current_progress / self.achievement.threshold_value) * 100, 1), 100)

    def update_progress(self, value: int = 1):
        """Update progress and unlock if threshold met."""
        self.current_progress += value
        if self.current_progress >= self.achievement.threshold_value and not self.is_unlocked:
            self.is_unlocked = True
            from django.utils import timezone
            self.unlocked_at = timezone.now()
        self.save()

    @classmethod
    def check_and_unlock(cls, user, trigger_event: str, increment: int = 1):
        """Check all achievements with a given trigger event and update progress."""
        achievements = Achievement.objects.filter(trigger_event=trigger_event, is_active=True)
        for achievement in achievements:
            ua, created = cls.objects.get_or_create(user=user, achievement=achievement)
            if not ua.is_unlocked:
                ua.update_progress(increment)
