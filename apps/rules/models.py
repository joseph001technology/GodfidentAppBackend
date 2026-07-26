from django.db import models
from django.conf import settings
from django.utils import timezone


class RuleCategory(models.Model):
    """Category for organizing rules."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='rule_categories'
    )
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=20, blank=True, default='#6C5CE7')
    icon = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'rule_categories'
        ordering = ['name']
        unique_together = ['user', 'name']

    def __str__(self):
        return self.name


class Rule(models.Model):
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

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'rules'
        ordering = ['order', 'title']

    def __str__(self):
        return self.title

    @property
    def is_completed_today(self):
        return self.completions.filter(
            completed_date=timezone.now().date()
        ).exists()

    @property
    def current_streak(self):
        """Calculate consecutive completion days."""
        completions = self.completions.filter(is_completed=True).order_by('-completed_date')
        if not completions:
            return 0
        streak = 0
        today = timezone.now().date()
        for c in completions:
            if c.completed_date == today - timezone.timedelta(days=streak):
                streak += 1
            else:
                break
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
