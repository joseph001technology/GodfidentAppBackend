from django.db import models
from django.conf import settings
from django.utils import timezone

from apps.common.models import TimeStampedModel


class RuleCategory(TimeStampedModel):
    """Category for organizing Universal Rules (e.g. 'Money', 'Speech')."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='rule_categories'
    )
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=20, blank=True, default='#6C5CE7')
    icon = models.CharField(max_length=50, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'rule_categories'
        verbose_name_plural = 'Rule Categories'
        ordering = ['order', 'name']
        unique_together = ['user', 'name']

    def __str__(self):
        return self.name

    @property
    def rule_count(self):
        return self.rules.filter(is_archived=False).count()


class Rule(TimeStampedModel):
    """A permanent rule with daily completion tracking."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='rules'
    )
    category = models.ForeignKey(
        RuleCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='rules'
    )
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=20, blank=True, default='#6C5CE7')
    is_pinned = models.BooleanField(default=False)
    is_favorite = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    is_daily = models.BooleanField(default=True)

    class Meta:
        db_table = 'rules'
        ordering = ['order', 'title']
        indexes = [
            models.Index(fields=['user', 'is_archived']),
            models.Index(fields=['user', 'category']),
        ]

    def __str__(self):
        return self.title

    @property
    def is_completed_today(self):
        return self.completions.filter(
            completed_date=timezone.now().date(), is_completed=True
        ).exists()

    @property
    def current_streak(self):
        """Calculate consecutive completion days ending today (or yesterday, if today isn't done yet)."""
        completed_dates = set(
            self.completions.filter(is_completed=True).values_list('completed_date', flat=True)
        )
        if not completed_dates:
            return 0

        today = timezone.now().date()
        # Streak can still be "current" if yesterday was completed and today just hasn't happened yet.
        cursor = today if today in completed_dates else today - timezone.timedelta(days=1)
        if cursor not in completed_dates:
            return 0

        streak = 0
        while cursor in completed_dates:
            streak += 1
            cursor -= timezone.timedelta(days=1)
        return streak


class RuleCompletion(models.Model):
    """Daily completion record for a rule."""
    rule = models.ForeignKey(Rule, on_delete=models.CASCADE, related_name='completions')
    completed_date = models.DateField()
    is_completed = models.BooleanField(default=True)
    completed_at = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True)

    class Meta:
        db_table = 'rule_completions'
        unique_together = ['rule', 'completed_date']
        ordering = ['-completed_date']

    def __str__(self):
        return f'{self.rule.title[:30]} - {self.completed_date}'