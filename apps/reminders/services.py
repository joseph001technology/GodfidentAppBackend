"""Services for the Reminders app."""

from django.utils import timezone
from .models import Reminder, ReminderHistory


def complete_reminder(reminder: Reminder) -> Reminder:
    """Mark a reminder as completed and handle repeats."""
    reminder.mark_completed()
    ReminderHistory.objects.create(
        reminder=reminder,
        action='completed',
        note='Reminder completed.',
    )
    return reminder


def snooze_reminder(reminder: Reminder, snooze_minutes: int = 10) -> Reminder:
    """Snooze a reminder for a given number of minutes."""
    reminder.is_snoozed = True
    reminder.snooze_until = timezone.now() + timezone.timedelta(minutes=snooze_minutes)
    reminder.status = 'snoozed'
    reminder.save(update_fields=['is_snoozed', 'snooze_until', 'status'])
    ReminderHistory.objects.create(
        reminder=reminder,
        action='snoozed',
        note=f'Snoozed for {snooze_minutes} minutes.',
    )
    return reminder


def miss_reminder(reminder: Reminder) -> Reminder:
    """Mark a reminder as missed."""
    reminder.status = 'missed'
    reminder.save(update_fields=['status'])
    ReminderHistory.objects.create(reminder=reminder, action='missed')
    return reminder


def log_reminder_action(reminder: Reminder, action: str, note: str = '') -> ReminderHistory:
    return ReminderHistory.objects.create(
        reminder=reminder, action=action, note=note
    )
