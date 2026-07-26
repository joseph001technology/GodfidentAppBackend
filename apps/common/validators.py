"""Custom validators for Godfident apps."""

from django.core.exceptions import ValidationError
import re


def validate_hex_color(value):
    """Validate that a value is a valid hex color code."""
    if not re.match(r'^#[0-9A-Fa-f]{6}$', value):
        raise ValidationError(f'{value} is not a valid hex color code.')


def validate_bible_reference(value):
    """Basic validation of a Bible reference format (e.g., John 3:16)."""
    if not re.match(r'^[A-Za-z\s]+ \d+:\d+(-\d+)?$', value.strip()):
        raise ValidationError(f'{value} is not a valid Bible reference.')

