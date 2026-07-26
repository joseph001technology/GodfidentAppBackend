from django.contrib import admin
from .models import BibleTranslation, BibleBook, BibleVerse, CrossReference, Bookmark, Highlight, VerseNote, ReadingProgress, FavoriteVerse, VerseCollection, VerseOfTheDay, ReadingGoal


@admin.register(BibleTranslation)
class BibleTranslationAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'language', 'is_active']
    list_editable = ['is_active']


@admin.register(BibleBook)
class BibleBookAdmin(admin.ModelAdmin):
    list_display = ['number', 'name', 'abbreviation', 'testament', 'chapter_count']
    list_filter = ['testament']


@admin.register(BibleVerse)
class BibleVerseAdmin(admin.ModelAdmin):
    list_display = ['translation', 'book', 'chapter', 'verse', 'text']
    list_filter = ['translation', 'book__testament']
    search_fields = ['text', 'book__name']
    raw_id_fields = ['translation', 'book']


@admin.register(CrossReference)
class CrossReferenceAdmin(admin.ModelAdmin):
    list_display = ['from_book', 'from_chapter', 'from_verse', 'to_book', 'to_chapter', 'to_verse']
    raw_id_fields = ['from_book', 'to_book']


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ['user', 'book', 'chapter', 'verse', 'created_at']
    list_filter = ['book__testament']
    search_fields = ['user__email', 'book__name']


@admin.register(Highlight)
class HighlightAdmin(admin.ModelAdmin):
    list_display = ['user', 'book', 'chapter', 'verse', 'color', 'created_at']
    list_filter = ['color']


@admin.register(VerseNote)
class VerseNoteAdmin(admin.ModelAdmin):
    list_display = ['user', 'book', 'chapter', 'verse', 'updated_at']
    search_fields = ['user__email', 'content']


@admin.register(VerseOfTheDay)
class VerseOfTheDayAdmin(admin.ModelAdmin):
    list_display = ['date', 'verse', 'is_active']
    list_filter = ['is_active']
    search_fields = ['verse__text', 'verse__book__name']
    date_hierarchy = 'date'


@admin.register(ReadingGoal)
class ReadingGoalAdmin(admin.ModelAdmin):
    list_display = ['user', 'chapters_target', 'period', 'is_active']
    list_filter = ['period', 'is_active']


@admin.register(ReadingProgress)
class ReadingProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'book', 'chapter', 'is_completed', 'last_read_at']


@admin.register(FavoriteVerse)
class FavoriteVerseAdmin(admin.ModelAdmin):
    list_display = ['user', 'book', 'chapter', 'verse']


@admin.register(VerseCollection)
class VerseCollectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'is_public', 'created_at']
