"""
Short-lived "vault" token for other people's prayers.

Other people's prayers are private to the person who wrote them down, so they
sit behind the same secret key that protects the blocked-website list (the
Website Protection Key). Entering that key at /api/focus/website-key/verify/
returns an ``unlock_token``; the app sends it back in the ``X-Prayer-Unlock``
header. The token is signed, tied to ONE user, and expires, so being logged in
is not enough to read those prayers.
"""
from django.core import signing

HEADER = 'HTTP_X_PRAYER_UNLOCK'  # request.META name of "X-Prayer-Unlock"
SALT = 'godfident.prayer.unlock.v1'
MAX_AGE_SECONDS = 30 * 60


def make_token(user):
    return signing.dumps({'u': str(user.pk)}, salt=SALT)


def is_open(request):
    """True when the request carries a valid, unexpired token for ITS OWN user."""
    token = request.META.get(HEADER, '')
    if not token or not getattr(request.user, 'is_authenticated', False):
        return False
    try:
        data = signing.loads(token, salt=SALT, max_age=MAX_AGE_SECONDS)
    except signing.BadSignature:  # also covers SignatureExpired
        return False
    return data.get('u') == str(request.user.pk)
