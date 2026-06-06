from rest_framework import serializers
from .models import (
    BibleTranslation, BibleBook, BibleVerse,
    CrossReference, Bookmark, Highlight, VerseNote,
)


class TranslationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BibleTranslation
        fields = ['id', 'code', 'name', 'full_name', 'language']


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = BibleBook
        fields = ['id', 'number', 'name', 'abbreviation', 'testament', 'chapter_count']


class VerseSerializer(serializers.ModelSerializer):
    book_name = serializers.CharField(source='book.name', read_only=True)
    translation_code = serializers.CharField(source='translation.code', read_only=True)
    reference = serializers.ReadOnlyField()

    class Meta:
        model = BibleVerse
        fields = ['id', 'translation_code', 'book_name', 'chapter', 'verse', 'text', 'reference']


class ChapterSerializer(serializers.Serializer):
    """Serializer for a full chapter response."""
    translation = serializers.CharField()
    book = serializers.CharField()
    book_number = serializers.IntegerField()
    chapter = serializers.IntegerField()
    total_chapters = serializers.IntegerField()
    verses = VerseSerializer(many=True)


class ParallelVerseSerializer(serializers.Serializer):
    """Verse shown in multiple translations side by side."""
    reference = serializers.CharField()
    book = serializers.CharField()
    chapter = serializers.IntegerField()
    verse = serializers.IntegerField()
    translations = serializers.DictField(child=serializers.CharField())


class CrossReferenceSerializer(serializers.ModelSerializer):
    to_book_name = serializers.CharField(source='to_book.name', read_only=True)
    reference = serializers.SerializerMethodField()

    class Meta:
        model = CrossReference
        fields = ['id', 'to_book_name', 'to_chapter', 'to_verse', 'to_verse_end', 'relevance_score', 'reference']

    def get_reference(self, obj):
        ref = f'{obj.to_book.name} {obj.to_chapter}:{obj.to_verse}'
        if obj.to_verse_end:
            ref += f'-{obj.to_verse_end}'
        return ref


class BookmarkSerializer(serializers.ModelSerializer):
    book_name = serializers.CharField(source='book.name', read_only=True)
    reference = serializers.SerializerMethodField()

    class Meta:
        model = Bookmark
        fields = ['id', 'book', 'book_name', 'chapter', 'verse', 'note', 'reference', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_reference(self, obj):
        return f'{obj.book.name} {obj.chapter}:{obj.verse}'


class HighlightSerializer(serializers.ModelSerializer):
    book_name = serializers.CharField(source='book.name', read_only=True)
    reference = serializers.SerializerMethodField()

    class Meta:
        model = Highlight
        fields = ['id', 'book', 'book_name', 'chapter', 'verse', 'color', 'note', 'reference', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_reference(self, obj):
        return f'{obj.book.name} {obj.chapter}:{obj.verse}'


class VerseNoteSerializer(serializers.ModelSerializer):
    book_name = serializers.CharField(source='book.name', read_only=True)

    class Meta:
        model = VerseNote
        fields = ['id', 'book', 'book_name', 'chapter', 'verse', 'content', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
