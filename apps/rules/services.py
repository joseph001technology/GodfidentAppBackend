"""Services for the Rules app."""

from django.utils import timezone
from .models import Rule, RuleCompletion


def get_or_create_today_completion(rule: Rule) -> RuleCompletion:
    """Get or create today's completion record for a rule."""
    completion, created = RuleCompletion.objects.get_or_create(
        rule=rule,
        completed_date=timezone.now().date(),
        defaults={'is_completed': True},
    )
    return completion


def toggle_today_completion(rule: Rule) -> tuple[bool, str]:
    """Toggle today's completion status for a rule."""
    completion, created = RuleCompletion.objects.get_or_create(
        rule=rule,
        completed_date=timezone.now().date(),
    )
    if created or not completion.is_completed:
        completion.is_completed = True
        completion.save(update_fields=['is_completed'])
        return True, 'Rule marked complete for today!'
    else:
        completion.is_completed = False
        completion.save(update_fields=['is_completed'])
        return False, 'Rule unmarked for today.'
