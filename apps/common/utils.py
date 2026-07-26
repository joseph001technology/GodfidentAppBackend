"""Shared utility functions."""

import uuid


def generate_uuid() -> str:
    return str(uuid.uuid4())


def truncate(text: str, max_length: int = 100) -> str:
    """Truncate text to max_length, appending '...' if needed."""
    if len(text) <= max_length:
        return text
    return text[:max_length].rsplit(' ', 1)[0] + '...'

