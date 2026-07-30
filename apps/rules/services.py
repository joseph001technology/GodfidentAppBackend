"""Services for the Rules app."""

from django.db import transaction
from django.utils import timezone

from .models import Rule, RuleCategory, RuleCompletion


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


@transaction.atomic
def reorder_rules(user, ordered_rule_ids: list) -> None:
    """Persist a new manual order for a user's rules (e.g. after a drag-reorder)."""
    rules = {r.id: r for r in Rule.objects.filter(user=user, id__in=ordered_rule_ids)}
    for index, rule_id in enumerate(ordered_rule_ids):
        rule = rules.get(rule_id)
        if rule is not None:
            rule.order = index
            rule.save(update_fields=['order'])


@transaction.atomic
def reorder_rule_categories(user, ordered_category_ids: list) -> None:
    """Persist a new manual order for a user's rule categories."""
    categories = {c.id: c for c in RuleCategory.objects.filter(user=user, id__in=ordered_category_ids)}
    for index, category_id in enumerate(ordered_category_ids):
        category = categories.get(category_id)
        if category is not None:
            category.order = index
            category.save(update_fields=['order'])