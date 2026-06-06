import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.utils import timezone

from apps.prayer.models import Prayer, PrayerLog
from apps.devotionals.models import Devotional, DailyDevotional, SavedDevotional, DevotionalReadHistory
from tests.factories import UserFactory, PrayerFactory, DevotionalFactory, DevotionalCategoryFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def auth_client(user):
    client = APIClient()
    resp = client.post(reverse('login'), {'email': user.email, 'password': 'TestPass123!'})
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {resp.data["access"]}')
    return client


# ─── Prayer Tests ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPrayer:
    def test_create_prayer_request(self, auth_client, user):
        response = auth_client.post(reverse('prayer-list'), {
            'title': 'Healing for my mother',
            'content': 'Please pray for my mother who is sick.',
            'prayer_type': 'request',
        })
        assert response.status_code == status.HTTP_201_CREATED
        assert Prayer.objects.filter(user=user, title='Healing for my mother').exists()

    def test_list_prayers(self, auth_client, user):
        PrayerFactory(user=user)
        PrayerFactory(user=user)
        response = auth_client.get(reverse('prayer-list'))
        assert response.status_code == status.HTTP_200_OK
        data = response.data.get('results', response.data)
        assert len(data) == 2

    def test_cannot_see_others_prayers(self, auth_client, user):
        other = UserFactory()
        PrayerFactory(user=other)
        response = auth_client.get(reverse('prayer-list'))
        data = response.data.get('results', response.data)
        assert len(data) == 0

    def test_mark_prayer_answered(self, auth_client, user):
        prayer = PrayerFactory(user=user)
        response = auth_client.post(
            reverse('prayer-mark-answered', args=[prayer.id]),
            {'note': 'God answered this prayer!'}
        )
        assert response.status_code == status.HTTP_200_OK
        prayer.refresh_from_db()
        assert prayer.status == 'answered'
        assert prayer.answered_note == 'God answered this prayer!'
        assert prayer.answered_at is not None

    def test_log_prayer(self, auth_client, user):
        prayer = PrayerFactory(user=user)
        response = auth_client.post(
            reverse('prayer-log-prayer', args=[prayer.id]),
            {'note': 'Prayed at 7am'}
        )
        assert response.status_code == status.HTTP_200_OK
        assert PrayerLog.objects.filter(user=user, prayer=prayer).exists()

    def test_prayer_stats(self, auth_client, user):
        PrayerFactory(user=user, prayer_type='request', status='active')
        PrayerFactory(user=user, prayer_type='request', status='answered')
        PrayerFactory(user=user, prayer_type='praise', status='active')
        response = auth_client.get(reverse('prayer-stats'))
        assert response.status_code == status.HTTP_200_OK
        data = response.data['data']
        assert data['total'] == 3
        assert data['answered'] == 1

    def test_filter_prayers_by_type(self, auth_client, user):
        PrayerFactory(user=user, prayer_type='request')
        PrayerFactory(user=user, prayer_type='praise')
        response = auth_client.get(reverse('prayer-list'), {'prayer_type': 'request'})
        data = response.data.get('results', response.data)
        assert all(p['prayer_type'] == 'request' for p in data)

    def test_search_prayers(self, auth_client, user):
        PrayerFactory(user=user, title='Healing prayer', content='Lord heal my friend')
        PrayerFactory(user=user, title='Job opportunity', content='Lord open doors')
        response = auth_client.get(reverse('prayer-list'), {'search': 'healing'})
        data = response.data.get('results', response.data)
        assert len(data) == 1

    def test_update_prayer(self, auth_client, user):
        prayer = PrayerFactory(user=user, title='Old title')
        response = auth_client.patch(
            reverse('prayer-detail', args=[prayer.id]),
            {'title': 'Updated title'}
        )
        assert response.status_code == status.HTTP_200_OK
        prayer.refresh_from_db()
        assert prayer.title == 'Updated title'

    def test_delete_prayer(self, auth_client, user):
        prayer = PrayerFactory(user=user)
        response = auth_client.delete(reverse('prayer-detail', args=[prayer.id]))
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Prayer.objects.filter(id=prayer.id).exists()


# ─── Devotional Tests ──────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestDevotionals:
    def test_list_devotionals(self, auth_client):
        DevotionalFactory()
        DevotionalFactory()
        response = auth_client.get(reverse('devotional-list'))
        assert response.status_code == status.HTTP_200_OK
        data = response.data.get('results', response.data)
        assert len(data) == 2

    def test_unpublished_not_shown(self, auth_client):
        DevotionalFactory(is_published=True)
        DevotionalFactory(is_published=False)
        response = auth_client.get(reverse('devotional-list'))
        data = response.data.get('results', response.data)
        assert len(data) == 1

    def test_read_devotional_marks_history(self, auth_client, user):
        devotional = DevotionalFactory()
        auth_client.get(reverse('devotional-detail', args=[devotional.id]))
        assert DevotionalReadHistory.objects.filter(user=user, devotional=devotional).exists()

    def test_save_devotional(self, auth_client, user):
        devotional = DevotionalFactory()
        response = auth_client.post(reverse('devotional-save', args=[devotional.id]))
        assert response.status_code == status.HTTP_200_OK
        assert SavedDevotional.objects.filter(user=user, devotional=devotional).exists()

    def test_unsave_devotional(self, auth_client, user):
        devotional = DevotionalFactory()
        SavedDevotional.objects.create(user=user, devotional=devotional)
        response = auth_client.delete(reverse('devotional-unsave', args=[devotional.id]))
        assert response.status_code == status.HTTP_200_OK
        assert not SavedDevotional.objects.filter(user=user, devotional=devotional).exists()

    def test_saved_devotionals_list(self, auth_client, user):
        d1 = DevotionalFactory()
        d2 = DevotionalFactory()
        SavedDevotional.objects.create(user=user, devotional=d1)
        response = auth_client.get(reverse('saved-devotionals'))
        data = response.data.get('results', response.data)
        assert len(data) == 1

    def test_today_devotional_with_scheduled(self, auth_client):
        devotional = DevotionalFactory()
        DailyDevotional.objects.create(date=timezone.now().date(), devotional=devotional)
        response = auth_client.get(reverse('today-devotional'))
        assert response.status_code == status.HTTP_200_OK

    def test_today_devotional_fallback(self, auth_client):
        DevotionalFactory()
        response = auth_client.get(reverse('today-devotional'))
        assert response.status_code == status.HTTP_200_OK

    def test_filter_by_category(self, auth_client):
        cat1 = DevotionalCategoryFactory()
        cat2 = DevotionalCategoryFactory()
        DevotionalFactory(category=cat1)
        DevotionalFactory(category=cat2)
        response = auth_client.get(reverse('devotional-list'), {'category': cat1.id})
        data = response.data.get('results', response.data)
        assert len(data) == 1

    def test_search_devotionals(self, auth_client):
        DevotionalFactory(title='Grace and Mercy')
        DevotionalFactory(title='Faith in Trials')
        response = auth_client.get(reverse('devotional-list'), {'search': 'grace'})
        data = response.data.get('results', response.data)
        assert len(data) == 1
