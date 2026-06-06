from django.db import models
from django.conf import settings


class BibleTranslation(models.Model):
    """Supported Bible translations."""
    code = models.CharField(max_length=10, unique=True)  # e.g. KJV, NIV
    name = models.CharField(max_length=100)
    full_name = models.CharField(max_length=200)
    language = models.CharField(max_length=50, default='English')
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'bible_translations'
        ordering = ['code']

    def __str__(self):
        return self.code


class BibleBook(models.Model):
    """Bible books (shared across translations)."""
    TESTAMENT_CHOICES = [('OT', 'Old Testament'), ('NT', 'New Testament')]

    number = models.PositiveSmallIntegerField(unique=True)  # 1-66
    name = models.CharField(max_length=50)
    abbreviation = models.CharField(max_length=10)
    testament = models.CharField(max_length=2, choices=TESTAMENT_CHOICES)
    chapter_count = models.PositiveSmallIntegerField()

    class Meta:
        db_table = 'bible_books'
        ordering = ['number']

    def __str__(self):
        return self.name


class BibleVerse(models.Model):
    """Individual Bible verses per translation."""
    translation = models.ForeignKey(BibleTranslation, on_delete=models.CASCADE, related_name='verses')
    book = models.ForeignKey(BibleBook, on_delete=models.CASCADE, related_name='verses')
    chapter = models.PositiveSmallIntegerField()
    verse = models.PositiveSmallIntegerField()
    text = models.TextField()

    class Meta:
        db_table = 'bible_verses'
        unique_together = ['translation', 'book', 'chapter', 'verse']
        indexes = [
            models.Index(fields=['translation', 'book', 'chapter']),
            models.Index(fields=['translation', 'book', 'chapter', 'verse']),
        ]

    def __str__(self):
        return f'{self.book.name} {self.chapter}:{self.verse} ({self.translation.code})'

    @property
    def reference(self):
        return f'{self.book.name} {self.chapter}:{self.verse}'


class CrossReference(models.Model):
    """Cross references between verses."""
    from_book = models.ForeignKey(BibleBook, on_delete=models.CASCADE, related_name='cross_refs_from')
    from_chapter = models.PositiveSmallIntegerField()
    from_verse = models.PositiveSmallIntegerField()
    to_book = models.ForeignKey(BibleBook, on_delete=models.CASCADE, related_name='cross_refs_to')
    to_chapter = models.PositiveSmallIntegerField()
    to_verse = models.PositiveSmallIntegerField()
    to_verse_end = models.PositiveSmallIntegerField(null=True, blank=True)  # for ranges
    relevance_score = models.FloatField(default=1.0)

    class Meta:
        db_table = 'cross_references'
        indexes = [
            models.Index(fields=['from_book', 'from_chapter', 'from_verse']),
        ]

    def __str__(self):
        return f'{self.from_book.name} {self.from_chapter}:{self.from_verse} → {self.to_book.name} {self.to_chapter}:{self.to_verse}'


class Bookmark(models.Model):
    """User bookmarks on verses."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookmarks')
    book = models.ForeignKey(BibleBook, on_delete=models.CASCADE)
    chapter = models.PositiveSmallIntegerField()
    verse = models.PositiveSmallIntegerField()
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'bookmarks'
        unique_together = ['user', 'book', 'chapter', 'verse']
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.email}: {self.book.name} {self.chapter}:{self.verse}'


class Highlight(models.Model):
    """User highlights on verses with color coding."""
    COLOR_CHOICES = [
        ('yellow', 'Yellow'),
        ('green', 'Green'),
        ('blue', 'Blue'),
        ('pink', 'Pink'),
        ('orange', 'Orange'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='highlights')
    book = models.ForeignKey(BibleBook, on_delete=models.CASCADE)
    chapter = models.PositiveSmallIntegerField()
    verse = models.PositiveSmallIntegerField()
    color = models.CharField(max_length=20, choices=COLOR_CHOICES, default='yellow')
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'highlights'
        unique_together = ['user', 'book', 'chapter', 'verse']
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.email}: {self.book.name} {self.chapter}:{self.verse} ({self.color})'


class VerseNote(models.Model):
    """User study notes on verses."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='verse_notes')
    book = models.ForeignKey(BibleBook, on_delete=models.CASCADE)
    chapter = models.PositiveSmallIntegerField()
    verse = models.PositiveSmallIntegerField()
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'verse_notes'
        ordering = ['-updated_at']

    def __str__(self):
        return f'{self.user.email}: Note on {self.book.name} {self.chapter}:{self.verse}'
