"""Link handling for Online Videos.

The server stores only the LINK to a video that lives on another platform
(never the video itself) and never fetches that link. These helpers only
validate and normalise text, so there is no network access here.
"""
import re
from urllib.parse import urlsplit, urlunsplit

from rest_framework.exceptions import ValidationError

MAX_URL_LENGTH = 2000

# Per-user ceilings keep one account from filling the shared database
# (the free PostgreSQL tiers have small quotas). Saved links are tiny.
MAX_VIDEOS_PER_USER = 5000
MAX_COLLECTIONS_PER_USER = 200

PLATFORMS = ('youtube', 'instagram', 'tiktok', 'facebook', 'vimeo', 'other')

_HOSTS = {
    'youtube': ('youtube.com', 'youtu.be', 'youtube-nocookie.com'),
    'instagram': ('instagram.com', 'instagr.am'),
    'tiktok': ('tiktok.com',),
    'facebook': ('facebook.com', 'fb.watch', 'fb.com'),
    'vimeo': ('vimeo.com',),
}

# What the phone's own parser produces, e.g. "youtube:dQw4w9WgXcQ" or "url:example.com/v/1".
_KNOWN_KEY = re.compile(r'^(youtube|instagram|tiktok|facebook|vimeo):[A-Za-z0-9_\-./]{1,120}$')
_URL_KEY = re.compile(r'^url:[\x21-\x7e]{1,280}$')


def clean_url(raw: str) -> str:
    """Returns the link without fragment/whitespace, or raises ValidationError."""
    url = (raw or '').strip()
    if not url or len(url) > MAX_URL_LENGTH:
        raise ValidationError('Enter a link that starts with https://')
    if re.search(r'\s', url):
        raise ValidationError('A link cannot contain spaces.')
    parts = urlsplit(url)
    if parts.scheme.lower() not in ('http', 'https') or not parts.hostname:
        raise ValidationError('Enter a link that starts with https://')
    if parts.username or parts.password:
        raise ValidationError('That link contains a sign-in; remove it and try again.')
    return urlunsplit((parts.scheme.lower(), parts.netloc, parts.path, parts.query, ''))


def _host(url: str) -> str:
    h = (urlsplit(url).hostname or '').lower()
    return h[4:] if h.startswith('www.') else h


def detect_platform(url: str) -> str:
    """The platform is decided here from the address; the phone's guess is not trusted."""
    h = _host(url)
    for platform, hosts in _HOSTS.items():
        if any(h == d or h.endswith('.' + d) for d in hosts):
            return platform
    return 'other'


def make_dedupe_key(url: str, platform: str, client_key: str = '') -> str:
    """The identity of a video, so the same video is saved once per user however the link was shared.

    The phone works the key out (it understands share links, short links and tracking
    parameters). It is accepted only if it has the expected shape and agrees with the
    platform found here; otherwise a key is made from the address itself.
    """
    k = (client_key or '').strip()
    if platform != 'other' and _KNOWN_KEY.match(k) and k.split(':', 1)[0] == platform:
        return k
    if platform == 'other' and _URL_KEY.match(k):
        return k
    parts = urlsplit(url)
    key = 'url:' + _host(url) + parts.path.rstrip('/') + (('?' + parts.query) if parts.query else '')
    return key[:300]
