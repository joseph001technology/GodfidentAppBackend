"""Central place every other app calls into for notification-related logic.

Two things live here, matching what was actually scoped:

1. Reminders (automatic + user-defined) - this app only stores *what* should
   be scheduled. Firing happens entirely on-device via
   flutter_local_notifications, so it keeps working offline. There is
   deliberately no backend push/Celery dispatch for these - that's real
   infra (Celery Beat, timezone handling, retry logic) for something local
   scheduling already covers, so it's left out of v1.

2. Backend-stored "soft" notifications (streak congrats, prayer milestones)
   - these depend on server-side state at the moment they're triggered, so
   they can't be pre-scheduled on-device. They're logged to the in-app
   Notification history and, if the user has a registered device, also sent
   as a real push via FCM - this part is a nice-to-have, not load-bearing,
   since it's a single fire-and-forget call, not a polling system.
"""

import logging
from datetime import time as time_cls

from .models import Notification, Reminder
from . import fcm

logger = logging.getLogger(__name__)

STREAK_MILESTONES = [3, 7, 14, 30, 60, 100, 200, 365]
PRAYERS_ANSWERED_MILESTONES = [5, 10, 25, 50, 100]

DEFAULT_REMINDERS = [
    {
        'title': 'Morning Prayer', 'message': 'Start your day with God.',
        'activity_type': 'prayer', 'time': time_cls(6, 0), 'icon': 'pray',
    },
    {
        'title': 'Evening Reading', 'message': 'Spend a few minutes in the Word.',
        'activity_type': 'bible', 'time': time_cls(20, 0), 'icon': 'book',
    },
]


# --- Reminders (automatic + user-defined) ---

def seed_default_reminders(user) -> None:
    """Create the two automatic reminders for a new user. Editable/toggleable
    after creation like any other reminder - just not deletable."""
    for d in DEFAULT_REMINDERS:
        Reminder.objects.get_or_create(
            user=user, activity_type=d['activity_type'], is_system_default=True,
            defaults={
                'title': d['title'], 'message': d['message'],
                'time': d['time'], 'icon': d['icon'], 'days_of_week': [],
            },
        )


def toggle_reminder_active(reminder: Reminder) -> Reminder:
    reminder.is_active = not reminder.is_active
    reminder.save(update_fields=['is_active'])
    return reminder


# --- Backend-stored non-essential notifications ---

def send_notification(user, notification_type: str, title: str, body: str,
                       data: dict | None = None, push: bool = True) -> Notification:
    """Always logs to the in-app Notification history; optionally also sends
    a real push via FCM if the user has an active device registered."""
    notification = Notification.objects.create(
        user=user, notification_type=notification_type,
        title=title, body=body, data=data or {},
    )
    if push:
        try:
            fcm.send_push_to_user(user, title, body, data)
        except Exception:
            # Push is a nice-to-have - never let a failed push break the
            # calling flow (e.g. a habit check-in) or the Notification row
            # that was already saved above.
            logger.exception('FCM push failed for user %s, notification still logged', user.id)
    return notification


def notify_streak_milestone(habit, streak_count: int) -> Notification | None:
    """Called from apps.habits.services right after a habit is marked done,
    if the new current_streak lands exactly on a milestone. Never blocks the
    check-in flow - this is encouragement, not core functionality."""
    if streak_count not in STREAK_MILESTONES:
        return None
    return send_notification(
        user=habit.user,
        notification_type='streak',
        title=f'streak milestone: {streak_count}-day {habit.name}',
        body=f"You've kept up {habit.name.lower()} for {streak_count} days in a row. Keep going.",
        data={'habit_id': habit.id, 'streak_count': streak_count},
    )


def notify_prayer_answered_milestone(user, answered_count: int) -> Notification | None:
    """Called from apps.prayer.services after a prayer entry is marked answered."""
    if answered_count not in PRAYERS_ANSWERED_MILESTONES:
        return None
    return send_notification(
        user=user,
        notification_type='achievement',
        title=f'{answered_count} answered prayers',
        body=f"You've marked {answered_count} prayers as answered.",
        data={'answered_count': answered_count},
    )
