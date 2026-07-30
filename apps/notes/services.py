"""Services for the Notes app - business logic lives here."""

from django.db import transaction

from .models import Note, NoteVersion, Rule, RuleCategory


# ---------------------------------------------------------------------------
# General notes
# ---------------------------------------------------------------------------

def create_note_version(note: Note) -> NoteVersion:
    """Create a version snapshot of a note before updating."""
    return NoteVersion.objects.create(
        note=note,
        version=note.version,
        title=note.title,
        content=note.content,
    )


def update_note(note: Note, validated_data: dict) -> Note:
    """Update a note with version tracking."""
    create_note_version(note)
    for attr, value in validated_data.items():
        setattr(note, attr, value)
    note.version += 1
    note.save()
    return note


def archive_note(note: Note) -> Note:
    """Archive a note."""
    note.archive()
    return note


def restore_note(note: Note) -> Note:
    """Restore an archived note."""
    note.restore()
    return note


# ---------------------------------------------------------------------------
# Universal Rules
# ---------------------------------------------------------------------------

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