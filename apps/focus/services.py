"""Services for Focus Mode app."""

from django.utils import timezone
from .models import FocusSession, BlockedAttempt


def start_session(user) -> FocusSession:
    """Start a new focus session."""
    # End any active sessions first
    FocusSession.objects.filter(user=user, status='active').update(status='interrupted')
    return FocusSession.objects.create(user=user)


def end_session(session: FocusSession, status='completed') -> FocusSession:
    """End a focus session."""
    session.end_session(status)
    return session


def log_blocked_attempt(user, target_type, target_name, session=None) -> BlockedAttempt:
    """Log a blocked attempt and increment session counter."""
    attempt = BlockedAttempt.objects.create(
        user=user,
        session=session,
        target_type=target_type,
        target_name=target_name,
    )
    if session and session.status == 'active':
        session.blocked_attempts += 1
        session.save(update_fields=['blocked_attempts'])
    return attempt


def get_focus_stats(user):
    """Get aggregated focus statistics."""
    sessions = FocusSession.objects.filter(user=user)
    total_sessions = sessions.count()
    completed = sessions.filter(status='completed').count()
    total_minutes = sum(s.duration_minutes for s in sessions.filter(status='completed'))
    total_blocked = sum(s.blocked_attempts for s in sessions.all())
    total_time_saved = total_blocked * 2  # 2 min per blocked attempt

    # This week
    week_start = timezone.now().date() - timezone.timedelta(days=timezone.now().weekday())
    week_sessions = sessions.filter(started_at__date__gte=week_start)
    week_minutes = sum(s.duration_minutes for s in week_sessions.filter(status='completed'))

    # Current streak (days with at least one session)
    streak = 0
    from datetime import timedelta
    day = timezone.now().date()
    while FocusSession.objects.filter(
        user=user, started_at__date=day, status='completed'
    ).exists():
        streak += 1
        day -= timedelta(days=1)

    return {
        'total_sessions': total_sessions,
        'completed_sessions': completed,
        'completion_rate': round((completed / total_sessions * 100), 1) if total_sessions else 0,
        'total_focus_minutes': total_minutes,
        'total_focus_hours': round(total_minutes / 60, 1),
        'total_blocked_attempts': total_blocked,
        'total_time_saved_minutes': total_time_saved,
        'this_week_minutes': week_minutes,
        'current_streak': streak,
    }
