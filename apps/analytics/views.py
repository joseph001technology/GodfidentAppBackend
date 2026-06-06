from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Count, Sum
from datetime import timedelta, date
import calendar

from .models import ReadingActivity, DailyStats
from apps.prayer.models import Prayer, PrayerLog
from apps.reading_plans.models import ReadingStreak, UserReadingPlan
from apps.devotionals.models import DevotionalReadHistory
from apps.ai_assistant.models import BibleStudySession
from apps.bible.models import Bookmark, Highlight


class DashboardView(APIView):
    """GET /analytics/dashboard/ - full spiritual growth dashboard"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        # Reading streak
        streak_data = {'current_streak': 0, 'longest_streak': 0, 'total_days_read': 0}
        try:
            streak = user.reading_streak
            streak_data = {
                'current_streak': streak.current_streak,
                'longest_streak': streak.longest_streak,
                'total_days_read': streak.total_days_read,
            }
        except Exception:
            pass

        # Reading this month
        chapters_this_month = ReadingActivity.objects.filter(
            user=user, read_at__date__gte=month_ago
        ).count()

        chapters_this_week = ReadingActivity.objects.filter(
            user=user, read_at__date__gte=week_ago
        ).count()

        # Prayer stats
        total_prayers = Prayer.objects.filter(user=user).count()
        answered_prayers = Prayer.objects.filter(user=user, status='answered').count()
        times_prayed = PrayerLog.objects.filter(user=user).count()

        # Devotionals
        devotionals_read = DevotionalReadHistory.objects.filter(user=user).count()
        devotionals_this_week = DevotionalReadHistory.objects.filter(
            user=user, read_at__date__gte=week_ago
        ).count()

        # Study sessions
        study_sessions = BibleStudySession.objects.filter(user=user).count()

        # Active reading plans
        active_plans = UserReadingPlan.objects.filter(user=user, status='active').count()
        completed_plans = UserReadingPlan.objects.filter(user=user, status='completed').count()

        # Bookmarks and highlights
        bookmarks = Bookmark.objects.filter(user=user).count()
        highlights = Highlight.objects.filter(user=user).count()

        return Response({
            'success': True,
            'data': {
                'reading': {
                    'streak': streak_data,
                    'chapters_this_week': chapters_this_week,
                    'chapters_this_month': chapters_this_month,
                },
                'prayer': {
                    'total_prayers': total_prayers,
                    'answered_prayers': answered_prayers,
                    'answer_rate': round((answered_prayers / total_prayers * 100) if total_prayers else 0, 1),
                    'times_prayed': times_prayed,
                },
                'devotionals': {
                    'total_read': devotionals_read,
                    'this_week': devotionals_this_week,
                },
                'study': {
                    'ai_sessions': study_sessions,
                },
                'plans': {
                    'active': active_plans,
                    'completed': completed_plans,
                },
                'annotations': {
                    'bookmarks': bookmarks,
                    'highlights': highlights,
                },
            }
        })


class ReadingHeatmapView(APIView):
    """GET /analytics/heatmap/?days=365 - GitHub-style reading heatmap data"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        days = int(request.query_params.get('days', 365))
        days = min(days, 365)
        user = request.user
        start_date = timezone.now().date() - timedelta(days=days)

        activities = ReadingActivity.objects.filter(
            user=user, read_at__date__gte=start_date
        ).extra(select={'day': 'date(read_at)'}).values('day').annotate(count=Count('id'))

        heatmap = {str(item['day']): item['count'] for item in activities}

        return Response({
            'success': True,
            'data': {
                'start_date': str(start_date),
                'end_date': str(timezone.now().date()),
                'heatmap': heatmap,
            }
        })


class WeeklyReportView(APIView):
    """GET /analytics/weekly/ - this week's summary"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())

        days_data = []
        for i in range(7):
            day = week_start + timedelta(days=i)
            chapters = ReadingActivity.objects.filter(user=user, read_at__date=day).count()
            prayers = PrayerLog.objects.filter(user=user, prayed_at__date=day).count()
            devotionals = DevotionalReadHistory.objects.filter(user=user, read_at__date=day).count()
            days_data.append({
                'date': str(day),
                'day_name': day.strftime('%A'),
                'chapters_read': chapters,
                'prayers_logged': prayers,
                'devotionals_read': devotionals,
                'is_today': day == today,
            })

        return Response({
            'success': True,
            'data': {
                'week_start': str(week_start),
                'week_end': str(week_start + timedelta(days=6)),
                'days': days_data,
                'totals': {
                    'chapters': sum(d['chapters_read'] for d in days_data),
                    'prayers': sum(d['prayers_logged'] for d in days_data),
                    'devotionals': sum(d['devotionals_read'] for d in days_data),
                }
            }
        })


class MonthlyReportView(APIView):
    """GET /analytics/monthly/?year=2025&month=6"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = timezone.now().date()
        year = int(request.query_params.get('year', today.year))
        month = int(request.query_params.get('month', today.month))

        _, days_in_month = calendar.monthrange(year, month)
        month_start = date(year, month, 1)
        month_end = date(year, month, days_in_month)

        chapters = ReadingActivity.objects.filter(
            user=user, read_at__date__range=[month_start, month_end]
        ).count()
        prayers = PrayerLog.objects.filter(
            user=user, prayed_at__date__range=[month_start, month_end]
        ).count()
        devotionals = DevotionalReadHistory.objects.filter(
            user=user, read_at__date__range=[month_start, month_end]
        ).count()
        study_sessions = BibleStudySession.objects.filter(
            user=user, created_at__date__range=[month_start, month_end]
        ).count()

        # Active days (days with at least one reading)
        active_days = ReadingActivity.objects.filter(
            user=user, read_at__date__range=[month_start, month_end]
        ).extra(select={'day': 'date(read_at)'}).values('day').distinct().count()

        return Response({
            'success': True,
            'data': {
                'year': year,
                'month': month,
                'month_name': calendar.month_name[month],
                'days_in_month': days_in_month,
                'active_days': active_days,
                'consistency_score': round((active_days / days_in_month) * 100, 1),
                'chapters_read': chapters,
                'prayers_logged': prayers,
                'devotionals_read': devotionals,
                'study_sessions': study_sessions,
            }
        })


class LogReadingActivityView(APIView):
    """POST /analytics/log-reading/ - called when user reads a chapter"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        book_name = request.data.get('book_name', '')
        chapter = request.data.get('chapter')
        translation = request.data.get('translation', 'KJV')

        if not all([book_name, chapter]):
            return Response({'success': False, 'message': 'book_name and chapter required.'}, status=400)

        ReadingActivity.objects.create(
            user=request.user,
            book_name=book_name,
            chapter=chapter,
            translation=translation,
        )

        # Update streak
        try:
            from apps.reading_plans.models import ReadingStreak
            streak, _ = ReadingStreak.objects.get_or_create(user=request.user)
            streak.update_streak()
        except Exception:
            pass

        return Response({'success': True, 'message': 'Reading activity logged.'})
