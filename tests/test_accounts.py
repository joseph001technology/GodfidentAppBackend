import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.utils import timezone
from datetime import timedelta

from apps.accounts.models import User, UserProfile, EmailVerificationToken, PasswordResetToken
from tests.factories import UserFactory, UserProfileFactory


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
    token = response.data['access']
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return client


# ─── Registration ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestRegistration:
    def test_register_creates_user(self, api_client):
        data = {
            'email': 'newuser@test.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'password': 'StrongPass123!',
            'password_confirm': 'StrongPass123!',
        }
        response = api_client.post(reverse('register'), data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['success'] is True
        assert User.objects.filter(email='newuser@test.com').exists()

    def test_register_creates_profile(self, api_client):
        data = {
            'email': 'newuser2@test.com',
            'password': 'StrongPass123!',
            'password_confirm': 'StrongPass123!',
        }
        api_client.post(reverse('register'), data)
        user = User.objects.get(email='newuser2@test.com')
        assert UserProfile.objects.filter(user=user).exists()

    def test_register_duplicate_email(self, api_client, user):
        data = {
            'email': user.email,
            'password': 'StrongPass123!',
            'password_confirm': 'StrongPass123!',
        }
        response = api_client.post(reverse('register'), data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_password_mismatch(self, api_client):
        data = {
            'email': 'test@test.com',
            'password': 'StrongPass123!',
            'password_confirm': 'WrongPass123!',
        }
        response = api_client.post(reverse('register'), data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_new_user_email_not_verified(self, api_client):
        data = {
            'email': 'unverified@test.com',
            'password': 'StrongPass123!',
            'password_confirm': 'StrongPass123!',
        }
        api_client.post(reverse('register'), data)
        user = User.objects.get(email='unverified@test.com')
        assert user.is_email_verified is False


# ─── Authentication ────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestAuthentication:
    def test_login_success(self, api_client, user):
        response = api_client.post(reverse('login'), {
            'email': user.email,
            'password': 'TestPass123!',
        })
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data

    def test_login_wrong_password(self, api_client, user):
        response = api_client.post(reverse('login'), {
            'email': user.email,
            'password': 'WrongPassword',
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_nonexistent_user(self, api_client):
        response = api_client.post(reverse('login'), {
            'email': 'nobody@test.com',
            'password': 'SomePass123!',
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ─── Email Verification ────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestEmailVerification:
    def test_verify_valid_token(self, api_client, user):
        token = EmailVerificationToken.objects.create(
            user=user,
            expires_at=timezone.now() + timedelta(hours=24),
        )
        response = api_client.post(reverse('verify-email'), {'token': str(token.token)})
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.is_email_verified is True

    def test_verify_expired_token(self, api_client, user):
        token = EmailVerificationToken.objects.create(
            user=user,
            expires_at=timezone.now() - timedelta(hours=1),
        )
        response = api_client.post(reverse('verify-email'), {'token': str(token.token)})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_verify_used_token(self, api_client, user):
        token = EmailVerificationToken.objects.create(
            user=user,
            expires_at=timezone.now() + timedelta(hours=24),
            is_used=True,
        )
        response = api_client.post(reverse('verify-email'), {'token': str(token.token)})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_verify_invalid_token(self, api_client):
        response = api_client.post(reverse('verify-email'), {'token': 'invalid-uuid'})
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ─── Password Reset ────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPasswordReset:
    def test_forgot_password_returns_success_regardless_of_email(self, api_client):
        """Should not reveal if email exists."""
        response = api_client.post(reverse('forgot-password'), {'email': 'notexist@test.com'})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True

    def test_reset_password_valid_token(self, api_client, user):
        token = PasswordResetToken.objects.create(
            user=user,
            expires_at=timezone.now() + timedelta(hours=1),
        )
        response = api_client.post(reverse('reset-password'), {
            'token': str(token.token),
            'new_password': 'NewStrongPass123!',
            'new_password_confirm': 'NewStrongPass123!',
        })
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.check_password('NewStrongPass123!')

    def test_reset_password_expired_token(self, api_client, user):
        token = PasswordResetToken.objects.create(
            user=user,
            expires_at=timezone.now() - timedelta(minutes=1),
        )
        response = api_client.post(reverse('reset-password'), {
            'token': str(token.token),
            'new_password': 'NewStrongPass123!',
            'new_password_confirm': 'NewStrongPass123!',
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ─── User Profile ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestUserProfile:
    def test_get_me(self, auth_client, user):
        response = auth_client.get(reverse('me'))
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == user.email

    def test_update_profile(self, auth_client, user):
        UserProfileFactory(user=user)
        response = auth_client.patch(reverse('profile'), {
            'preferred_translation': 'NIV',
            'timezone': 'Africa/Nairobi',
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.data['preferred_translation'] == 'NIV'

    def test_unauthenticated_cannot_access_me(self, api_client):
        response = api_client.get(reverse('me'))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_change_password(self, auth_client, user):
        response = auth_client.post(reverse('change-password'), {
            'old_password': 'TestPass123!',
            'new_password': 'NewStrongPass123!',
            'new_password_confirm': 'NewStrongPass123!',
        })
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.check_password('NewStrongPass123!')

    def test_change_password_wrong_old(self, auth_client):
        response = auth_client.post(reverse('change-password'), {
            'old_password': 'WrongOldPass!',
            'new_password': 'NewStrongPass123!',
            'new_password_confirm': 'NewStrongPass123!',
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
