import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.utils import timezone
from datetime import timedelta

from apps.analytics.models import ReadingActivity
from apps.notifications.models import Notification
from tests.factories import UserFactory


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def auth_client(user):
    client = APIClient()
    resp = client.post(reverse('login'), {'email': user.email, 'password': 'TestPass123!'})
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {resp.data["access"]}')
    return client


# ─── Analytics ─────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestAnalytics:
    def test_dashboard_returns_data(self, auth_client):
        response = auth_client.get(reverse('analytics-dashboard'))
        assert response.status_code == status.HTTP_200_OK
        data = response.data['data']
        assert 'reading' in data
        assert 'prayer' in data
        assert 'devotionals' in data

    def test_log_reading_activity(self, auth_client, user):
        response = auth_client.post(reverse('log-reading'), {
            'book_name': 'John', 'chapter': 3, 'translation': 'KJV'
        })
        assert response.status_code == status.HTTP_200_OK
        assert ReadingActivity.objects.filter(user=user, book_name='John', chapter=3).exists()

    def test_log_reading_missing_params(self, auth_client):
        response = auth_client.post(reverse('log-reading'), {'book_name': 'John'})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_heatmap_returns_data(self, auth_client, user):
        today = timezone.now().date()
        ReadingActivity.objects.create(user=user, book_name='John', chapter=1, translation='KJV')
        response = auth_client.get(reverse('reading-heatmap'), {'days': 30})
        assert response.status_code == status.HTTP_200_OK
        assert 'heatmap' in response.data['data']
        assert str(today) in response.data['data']['heatmap']

    def test_weekly_report(self, auth_client, user):
        ReadingActivity.objects.create(user=user, book_name='Genesis', chapter=1, translation='KJV')
        response = auth_client.get(reverse('weekly-report'))
        assert response.status_code == status.HTTP_200_OK
        assert 'days' in response.data['data']
        assert len(response.data['data']['days']) == 7

    def test_monthly_report(self, auth_client, user):
        today = timezone.now().date()
        response = auth_client.get(reverse('monthly-report'), {
            'year': today.year, 'month': today.month
        })
        assert response.status_code == status.HTTP_200_OK
        data = response.data['data']
        assert 'chapters_read' in data
        assert 'consistency_score' in data

    def test_dashboard_counts_are_accurate(self, auth_client, user):
        ReadingActivity.objects.create(user=user, book_name='John', chapter=1, translation='KJV')
        ReadingActivity.objects.create(user=user, book_name='John', chapter=2, translation='KJV')
        response = auth_client.get(reverse('analytics-dashboard'))
        data = response.data['data']
        assert data['reading']['chapters_this_month'] == 2


# ─── Notifications ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestNotifications:
    def test_list_notifications(self, auth_client, user):
        Notification.objects.create(
            user=user,
            notification_type='general',
            title='Welcome to Godfident!',
            body='Start your journey today.',
        )
        response = auth_client.get(reverse('notification-list'))
        assert response.status_code == status.HTTP_200_OK
        data = response.data.get('results', response.data)
        assert len(data) == 1

    def test_unread_filter(self, auth_client, user):
        Notification.objects.create(user=user, notification_type='general', title='Unread', body='test')
        Notification.objects.create(user=user, notification_type='general', title='Read', body='test', is_read=True)
        response = auth_client.get(reverse('notification-list'), {'unread': 'true'})
        data = response.data.get('results', response.data)
        assert len(data) == 1
        assert data[0]['is_read'] is False

    def test_mark_notification_read(self, auth_client, user):
        notif = Notification.objects.create(
            user=user, notification_type='general', title='Test', body='body'
        )
        response = auth_client.post(reverse('notification-mark-read', args=[notif.id]))
        assert response.status_code == status.HTTP_200_OK
        notif.refresh_from_db()
        assert notif.is_read is True
        assert notif.read_at is not None

    def test_mark_all_read(self, auth_client, user):
        Notification.objects.bulk_create([
            Notification(user=user, notification_type='general', title=f'N{i}', body='b')
            for i in range(5)
        ])
        response = auth_client.post(reverse('notification-mark-all-read'))
        assert response.status_code == status.HTTP_200_OK
        assert Notification.objects.filter(user=user, is_read=False).count() == 0

    def test_unread_count(self, auth_client, user):
        Notification.objects.bulk_create([
            Notification(user=user, notification_type='general', title=f'N{i}', body='b')
            for i in range(3)
        ])
        response = auth_client.get(reverse('notification-unread-count'))
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 3

    def test_user_cannot_see_others_notifications(self, auth_client, user):
        other = UserFactory()
        Notification.objects.create(user=other, notification_type='general', title='Secret', body='body')
        response = auth_client.get(reverse('notification-list'))
        data = response.data.get('results', response.data)
        assert len(data) == 0
