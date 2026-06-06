from rest_framework import viewsets, generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter

from .models import BibleTranslation, BibleBook, BibleVerse, CrossReference, Bookmark, Highlight, VerseNote
from .serializers import (
    TranslationSerializer, BookSerializer, VerseSerializer, ChapterSerializer,
    ParallelVerseSerializer, CrossReferenceSerializer,
    BookmarkSerializer, HighlightSerializer, VerseNoteSerializer,
)


class TranslationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BibleTranslation.objects.filter(is_active=True)
    serializer_class = TranslationSerializer
    permission_classes = [AllowAny]


class BookViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BibleBook.objects.all()
    serializer_class = BookSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['testament']
    search_fields = ['name', 'abbreviation']


class VerseView(generics.RetrieveAPIView):
    """GET /bible/verse/?translation=KJV&book=John&chapter=3&verse=16"""
    permission_classes = [IsAuthenticated]
    serializer_class = VerseSerializer

    def get(self, request):
        translation_code = request.query_params.get('translation', 'KJV')
        book_name = request.query_params.get('book', '')
        chapter = request.query_params.get('chapter')
        verse_num = request.query_params.get('verse')

        if not all([book_name, chapter, verse_num]):
            return Response(
                {'success': False, 'message': 'book, chapter, and verse are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            verse = BibleVerse.objects.select_related('translation', 'book').get(
                translation__code__iexact=translation_code,
                book__name__iexact=book_name,
                chapter=chapter,
                verse=verse_num,
            )
            return Response({'success': True, 'data': VerseSerializer(verse).data})
        except BibleVerse.DoesNotExist:
            return Response(
                {'success': False, 'message': 'Verse not found.'},
                status=status.HTTP_404_NOT_FOUND
            )


class ChapterView(generics.RetrieveAPIView):
    """GET /bible/chapter/?translation=KJV&book=John&chapter=3"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        translation_code = request.query_params.get('translation', 'KJV')
        book_name = request.query_params.get('book', '')
        chapter = request.query_params.get('chapter')

        if not all([book_name, chapter]):
            return Response(
                {'success': False, 'message': 'book and chapter are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            book = BibleBook.objects.get(name__iexact=book_name)
            translation = BibleTranslation.objects.get(code__iexact=translation_code)
        except (BibleBook.DoesNotExist, BibleTranslation.DoesNotExist):
            return Response(
                {'success': False, 'message': 'Book or translation not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        verses = BibleVerse.objects.filter(
            translation=translation, book=book, chapter=chapter
        ).select_related('book', 'translation').order_by('verse')

        if not verses.exists():
            return Response(
                {'success': False, 'message': 'Chapter not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        data = {
            'translation': translation.code,
            'book': book.name,
            'book_number': book.number,
            'chapter': int(chapter),
            'total_chapters': book.chapter_count,
            'verses': VerseSerializer(verses, many=True).data,
        }
        return Response({'success': True, 'data': data})


class ParallelVerseView(generics.RetrieveAPIView):
    """GET /bible/parallel/?book=John&chapter=3&verse=16&translations=KJV,NIV,ESV"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        book_name = request.query_params.get('book', '')
        chapter = request.query_params.get('chapter')
        verse_num = request.query_params.get('verse')
        translation_codes = request.query_params.get('translations', 'KJV,NIV').split(',')

        if not all([book_name, chapter, verse_num]):
            return Response(
                {'success': False, 'message': 'book, chapter, and verse are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            book = BibleBook.objects.get(name__iexact=book_name)
        except BibleBook.DoesNotExist:
            return Response({'success': False, 'message': 'Book not found.'}, status=404)

        translations_data = {}
        for code in translation_codes:
            code = code.strip().upper()
            try:
                verse = BibleVerse.objects.get(
                    translation__code=code, book=book, chapter=chapter, verse=verse_num
                )
                translations_data[code] = verse.text
            except BibleVerse.DoesNotExist:
                translations_data[code] = None

        data = {
            'reference': f'{book.name} {chapter}:{verse_num}',
            'book': book.name,
            'chapter': int(chapter),
            'verse': int(verse_num),
            'translations': translations_data,
        }
        return Response({'success': True, 'data': data})


class CrossReferenceView(generics.ListAPIView):
    """GET /bible/cross-references/?book=John&chapter=3&verse=16"""
    serializer_class = CrossReferenceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        book_name = self.request.query_params.get('book', '')
        chapter = self.request.query_params.get('chapter')
        verse_num = self.request.query_params.get('verse')

        if not all([book_name, chapter, verse_num]):
            return CrossReference.objects.none()

        return CrossReference.objects.filter(
            from_book__name__iexact=book_name,
            from_chapter=chapter,
            from_verse=verse_num,
        ).select_related('to_book').order_by('-relevance_score')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({'success': True, 'data': serializer.data})


class SearchVerseView(generics.ListAPIView):
    """GET /bible/search/?q=love&translation=KJV&testament=NT"""
    serializer_class = VerseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        q = self.request.query_params.get('q', '')
        translation = self.request.query_params.get('translation', 'KJV')
        testament = self.request.query_params.get('testament', '')

        qs = BibleVerse.objects.filter(
            translation__code__iexact=translation,
            text__icontains=q,
        ).select_related('book', 'translation')

        if testament:
            qs = qs.filter(book__testament=testament.upper())

        return qs.order_by('book__number', 'chapter', 'verse')[:50]


class BookmarkViewSet(viewsets.ModelViewSet):
    serializer_class = BookmarkSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Bookmark.objects.filter(user=self.request.user).select_related('book')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class HighlightViewSet(viewsets.ModelViewSet):
    serializer_class = HighlightSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['color']

    def get_queryset(self):
        return Highlight.objects.filter(user=self.request.user).select_related('book')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class VerseNoteViewSet(viewsets.ModelViewSet):
    serializer_class = VerseNoteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return VerseNote.objects.filter(user=self.request.user).select_related('book')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
