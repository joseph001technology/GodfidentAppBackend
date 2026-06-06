import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.utils import timezone

from apps.reading_plans.models import (
    ReadingPlan, ReadingPlanDay, UserReadingPlan, DayProgress, ReadingStreak
)
from tests.factories import UserFactory, ReadingPlanFactory


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def auth_client(user):
    client = APIClient()
    resp = client.post(reverse('login'), {'email': user.email, 'password': 'TestPass123!'})
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {resp.data["access"]}')
    return client


@pytest.fixture
def plan(db):
    p = ReadingPlanFactory(duration_days=3)
    for i in range(1, 4):
        ReadingPlanDay.objects.create(
            plan=p, day_number=i,
            title=f'Day {i}',
            readings=[{'book': 'John', 'chapter_start': i, 'chapter_end': i}]
        )
    return p


# ─── Reading Plans ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestReadingPlans:
    def test_list_plans(self, auth_client, plan):
        response = auth_client.get(reverse('reading-plan-list'))
        assert response.status_code == status.HTTP_200_OK

    def test_get_plan_days(self, auth_client, plan):
        response = auth_client.get(reverse('reading-plan-days', args=[plan.id]))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) == 3

    def test_enroll_in_plan(self, auth_client, user, plan):
        response = auth_client.post(reverse('user-reading-plan-list'), {'plan_id': plan.id})
        assert response.status_code == status.HTTP_201_CREATED
        assert UserReadingPlan.objects.filter(user=user, plan=plan).exists()

    def test_cannot_enroll_twice(self, auth_client, user, plan):
        UserReadingPlan.objects.create(user=user, plan=plan, status='active')
        response = auth_client.post(reverse('user-reading-plan-list'), {'plan_id': plan.id})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_complete_day(self, auth_client, user, plan):
        user_plan = UserReadingPlan.objects.create(user=user, plan=plan, current_day=1)
        response = auth_client.post(
            reverse('user-reading-plan-complete-day', args=[user_plan.id]),
            {'day_number': 1}
        )
        assert response.status_code == status.HTTP_200_OK
        assert DayProgress.objects.filter(user_plan=user_plan, is_completed=True).count() == 1
        user_plan.refresh_from_db()
        assert user_plan.current_day == 2

    def test_completing_all_days_marks_plan_complete(self, auth_client, user, plan):
        user_plan = UserReadingPlan.objects.create(user=user, plan=plan, current_day=1)
        for day_num in range(1, 4):
            auth_client.post(
                reverse('user-reading-plan-complete-day', args=[user_plan.id]),
                {'day_number': day_num}
            )
        user_plan.refresh_from_db()
        assert user_plan.status == 'completed'
        assert user_plan.completed_at is not None

    def test_pause_plan(self, auth_client, user, plan):
        user_plan = UserReadingPlan.objects.create(user=user, plan=plan, status='active')
        response = auth_client.post(reverse('user-reading-plan-pause', args=[user_plan.id]))
        assert response.status_code == status.HTTP_200_OK
        user_plan.refresh_from_db()
        assert user_plan.status == 'paused'

    def test_resume_plan(self, auth_client, user, plan):
        user_plan = UserReadingPlan.objects.create(user=user, plan=plan, status='paused')
        response = auth_client.post(reverse('user-reading-plan-resume', args=[user_plan.id]))
        assert response.status_code == status.HTTP_200_OK
        user_plan.refresh_from_db()
        assert user_plan.status == 'active'

    def test_progress_percent(self, user, plan):
        user_plan = UserReadingPlan.objects.create(user=user, plan=plan)
        assert user_plan.progress_percent == 0.0
        day = plan.days.first()
        DayProgress.objects.create(user_plan=user_plan, plan_day=day, is_completed=True)
        assert user_plan.progress_percent == pytest.approx(33.3, abs=0.1)


# ─── Reading Streak ────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestReadingStreak:
    def test_streak_starts_at_zero(self, user):
        streak = ReadingStreak.objects.create(user=user)
        assert streak.current_streak == 0

    def test_first_read_sets_streak_to_one(self, user):
        streak = ReadingStreak.objects.create(user=user)
        streak.update_streak()
        assert streak.current_streak == 1
        assert streak.total_days_read == 1

    def test_consecutive_days_increase_streak(self, user):
        from datetime import timedelta
        streak = ReadingStreak.objects.create(
            user=user,
            current_streak=5,
            last_read_date=timezone.now().date() - timedelta(days=1),
            total_days_read=5,
        )
        streak.update_streak()
        assert streak.current_streak == 6

    def test_missed_day_resets_streak(self, user):
        from datetime import timedelta
        streak = ReadingStreak.objects.create(
            user=user,
            current_streak=10,
            last_read_date=timezone.now().date() - timedelta(days=3),
        )
        streak.update_streak()
        assert streak.current_streak == 1

    def test_longest_streak_is_tracked(self, user):
        from datetime import timedelta
        streak = ReadingStreak.objects.create(
            user=user,
            current_streak=14,
            longest_streak=14,
            last_read_date=timezone.now().date() - timedelta(days=1),
        )
        streak.update_streak()
        assert streak.longest_streak == 15

    def test_get_streak_endpoint(self, auth_client):
        response = auth_client.get(reverse('reading-streak'))
        assert response.status_code == status.HTTP_200_OK
        assert 'current_streak' in response.data['data']
