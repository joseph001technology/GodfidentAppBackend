from django.db import models
from django.conf import settings


class Folder(models.Model):
    """A folder for organizing notes."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='note_folders'
    )
    name = models.CharField(max_length=200)
    color = models.CharField(max_length=20, blank=True, default='#6C5CE7')
    icon = models.CharField(max_length=50, blank=True)
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='children'
    )
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'note_folders'
        ordering = ['order', 'name']
        unique_together = ['user', 'name', 'parent']

    def __str__(self):
        return self.name

    @property
    def note_count(self):
        return self.notes.count()


class Topic(models.Model):
    """A topic/tag for categorizing notes."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='topics'
    )
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=20, blank=True, default='#00B894')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'note_topics'
        ordering = ['name']
        unique_together = ['user', 'name']

    def __str__(self):
        return self.name


class Note(models.Model):
    """A rich personal note with Bible reference support."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notes'
    )
    folder = models.ForeignKey(
        Folder, on_delete=models.SET_NULL, null=True, blank=True, related_name='notes'
    )
    topics = models.ManyToManyField(Topic, blank=True, related_name='notes')

    title = models.CharField(max_length=500)
    content = models.TextField(blank=True)  # Rich text content (HTML/Markdown)

    # Bible references stored as JSON array: [{"book": "John", "chapter": 3, "verse": 16}, ...]
    bible_references = models.JSONField(default=list, blank=True)

    is_pinned = models.BooleanField(default=False)
    is_favorite = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)

    # Version history (optional, store JSON diffs)
    version = models.PositiveIntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    archived_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'notes'
        ordering = ['-is_pinned', '-updated_at']
        indexes = [
            models.Index(fields=['user', 'is_archived']),
            models.Index(fields=['user', 'is_favorite']),
            models.Index(fields=['user', 'is_pinned']),
            models.Index(fields=['user', 'updated_at']),
        ]

    def __str__(self):
        return self.title[:50]

    def archive(self):
        from django.utils import timezone
        self.is_archived = True
        self.archived_at = timezone.now()
        self.save(update_fields=['is_archived', 'archived_at'])

    def restore(self):
        self.is_archived = False
        self.archived_at = None
        self.save(update_fields=['is_archived', 'archived_at'])


class NoteVersion(models.Model):
    """Optional version history for notes."""
    note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name='versions')
    version = models.PositiveIntegerField()
    title = models.CharField(max_length=500)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'note_versions'
        ordering = ['-version']
        unique_together = ['note', 'version']

    def __str__(self):
        return f'{self.note.title[:30]} v{self.version}'
