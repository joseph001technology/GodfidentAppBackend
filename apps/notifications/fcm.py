"""Thin wrapper around firebase_admin.messaging.

Requires FIREBASE_CREDENTIALS_PATH (or equivalent) configured in settings and
firebase_admin initialized once at startup (typically in apps.py.ready() or
a management command) — not repeated here since it's project-wide setup,
not something this app should own.
"""

import logging

from .models import FCMDevice

logger = logging.getLogger(__name__)


def send_push_to_user(user, title: str, body: str, data: dict | None = None) -> int:
    """Send a push notification to every active device the user has registered.
    Returns the number of devices successfully notified. Any token Firebase
    reports as invalid/unregistered is deactivated so it stops being retried."""
    devices = list(FCMDevice.objects.filter(user=user, is_active=True))
    if not devices:
        return 0

    try:
        from firebase_admin import messaging
    except ImportError:
        logger.warning('firebase_admin not installed — skipping push, Notification row is still created.')
        return 0

    tokens = [d.token for d in devices]
    message = messaging.MulticastMessage(
        notification=messaging.Notification(title=title, body=body),
        data={k: str(v) for k, v in (data or {}).items()},
        tokens=tokens,
    )

    try:
        response = messaging.send_each_for_multicast(message)
    except Exception:
        logger.exception('FCM send failed for user %s', user.id)
        return 0

    # Deactivate tokens Firebase reports as dead, so we stop paying for retries on them.
    invalid_indexes = [
        i for i, r in enumerate(response.responses)
        if not r.success and getattr(r.exception, 'code', None) in ('UNREGISTERED', 'INVALID_ARGUMENT')
    ]
    if invalid_indexes:
        dead_tokens = [tokens[i] for i in invalid_indexes]
        FCMDevice.objects.filter(token__in=dead_tokens).update(is_active=False)

    return response.success_count
