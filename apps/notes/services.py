"""Services for the Notes app - business logic lives here."""

from .models import Note, NoteVersion


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