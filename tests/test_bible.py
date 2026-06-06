import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.bible.models import BibleBook, BibleTranslation, BibleVerse, Bookmark, Highlight, VerseNote
from tests.factories import UserFactory, BibleBookFactory, BibleTranslationFactory, BibleVerseFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def auth_client(user):
    client = APIClient()
    response = client.post(reverse('login'), {'email': user.email, 'password': 'TestPass123!'})
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {response.data["access"]}')
    return client


@pytest.fixture
def translation(db):
    return BibleTranslationFactory()


@pytest.fixture
def book(db):
    return BibleBookFactory(number=43, name='John', abbreviation='Joh', testament='NT', chapter_count=21)


@pytest.fixture
def verse(db, translation, book):
    return BibleVerseFactory(
        translation=translation, book=book, chapter=3, verse=16,
        text='For God so loved the world, that he gave his only begotten Son...'
    )


# ─── Translations & Books ──────────────────────────────────────────────────────

@pytest.mark.django_db
class TestBibleStructure:
    def test_list_translations(self, api_client, translation):
        response = api_client.get(reverse('translation-list'))
        assert response.status_code == status.HTTP_200_OK

    def test_list_books(self, api_client, book):
        response = api_client.get(reverse('book-list'))
        assert response.status_code == status.HTTP_200_OK

    def test_filter_books_by_testament(self, api_client, book):
        response = api_client.get(reverse('book-list'), {'testament': 'NT'})
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results'] if 'results' in response.data else response.data
        assert all(b['testament'] == 'NT' for b in results)


# ─── Verse & Chapter Access ────────────────────────────────────────────────────

@pytest.mark.django_db
class TestVerseAccess:
    def test_get_verse(self, auth_client, verse):
        response = auth_client.get(reverse('verse'), {
            'translation': 'KJV', 'book': 'John', 'chapter': 3, 'verse': 16
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'God so loved' in response.data['data']['text']

    def test_get_verse_missing_params(self, auth_client):
        response = auth_client.get(reverse('verse'), {'book': 'John'})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_verse_not_found(self, auth_client, translation, book):
        response = auth_client.get(reverse('verse'), {
            'translation': 'KJV', 'book': 'John', 'chapter': 99, 'verse': 99
        })
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_chapter(self, auth_client, verse):
        response = auth_client.get(reverse('chapter'), {
            'translation': 'KJV', 'book': 'John', 'chapter': 3
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['chapter'] == 3

    def test_unauthenticated_cannot_read_verse(self, api_client, verse):
        response = api_client.get(reverse('verse'), {
            'translation': 'KJV', 'book': 'John', 'chapter': 3, 'verse': 16
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ─── Parallel View ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestParallelView:
    def test_parallel_verse(self, auth_client, verse):
        response = auth_client.get(reverse('parallel'), {
            'book': 'John', 'chapter': 3, 'verse': 16, 'translations': 'KJV'
        })
        assert response.status_code == status.HTTP_200_OK
        assert 'KJV' in response.data['data']['translations']

    def test_parallel_missing_params(self, auth_client):
        response = auth_client.get(reverse('parallel'), {'book': 'John'})
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ─── Search ────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestBibleSearch:
    def test_search_verses(self, auth_client, verse):
        response = auth_client.get(reverse('search'), {'q': 'God so loved', 'translation': 'KJV'})
        assert response.status_code == status.HTTP_200_OK

    def test_search_requires_auth(self, api_client, verse):
        response = api_client.get(reverse('search'), {'q': 'love'})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ─── Bookmarks ─────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestBookmarks:
    def test_create_bookmark(self, auth_client, user, book):
        response = auth_client.post(reverse('bookmark-list'), {
            'book': book.id, 'chapter': 3, 'verse': 16, 'note': 'My favourite verse'
        })
        assert response.status_code == status.HTTP_201_CREATED
        assert Bookmark.objects.filter(user=user, book=book, chapter=3, verse=16).exists()

    def test_list_bookmarks(self, auth_client, user, book):
        Bookmark.objects.create(user=user, book=book, chapter=1, verse=1)
        response = auth_client.get(reverse('bookmark-list'))
        assert response.status_code == status.HTTP_200_OK

    def test_delete_bookmark(self, auth_client, user, book):
        bookmark = Bookmark.objects.create(user=user, book=book, chapter=3, verse=16)
        response = auth_client.delete(reverse('bookmark-detail', args=[bookmark.id]))
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_user_cannot_see_others_bookmarks(self, auth_client, book):
        other_user = UserFactory()
        Bookmark.objects.create(user=other_user, book=book, chapter=1, verse=1)
        response = auth_client.get(reverse('bookmark-list'))
        assert response.status_code == status.HTTP_200_OK
        data = response.data.get('results', response.data)
        assert len(data) == 0


# ─── Highlights ────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestHighlights:
    def test_create_highlight(self, auth_client, user, book):
        response = auth_client.post(reverse('highlight-list'), {
            'book': book.id, 'chapter': 3, 'verse': 16, 'color': 'yellow'
        })
        assert response.status_code == status.HTTP_201_CREATED

    def test_filter_highlights_by_color(self, auth_client, user, book):
        Highlight.objects.create(user=user, book=book, chapter=1, verse=1, color='yellow')
        Highlight.objects.create(user=user, book=book, chapter=1, verse=2, color='green')
        response = auth_client.get(reverse('highlight-list'), {'color': 'yellow'})
        data = response.data.get('results', response.data)
        assert all(h['color'] == 'yellow' for h in data)


# ─── Verse Notes ───────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestVerseNotes:
    def test_create_note(self, auth_client, user, book):
        response = auth_client.post(reverse('verse-note-list'), {
            'book': book.id, 'chapter': 3, 'verse': 16,
            'content': 'This is the most famous verse in the Bible.'
        })
        assert response.status_code == status.HTTP_201_CREATED

    def test_update_note(self, auth_client, user, book):
        note = VerseNote.objects.create(
            user=user, book=book, chapter=3, verse=16, content='Original note'
        )
        response = auth_client.patch(reverse('verse-note-detail', args=[note.id]), {
            'content': 'Updated note content'
        })
        assert response.status_code == status.HTTP_200_OK
        note.refresh_from_db()
        assert note.content == 'Updated note content'
