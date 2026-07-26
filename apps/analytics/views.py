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

class PrayerAnalyticsView(APIView):
    """GET /analytics/prayer/ - detailed prayer analytics."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        from apps.prayer.models import Prayer, PrayerLog, PrayerSession, PrayerJournal, PrayerStreak
        from datetime import timedelta

        week_ago = timezone.now().date() - timedelta(days=7)
        month_ago = timezone.now().date() - timedelta(days=30)

        total_prayers = Prayer.objects.filter(user=user).count()
        answered = Prayer.objects.filter(user=user, status='answered').count()
        active = Prayer.objects.filter(user=user, status='active').count()

        logs = PrayerLog.objects.filter(user=user)
        total_logs = logs.count()
        week_logs = logs.filter(prayed_at__date__gte=week_ago).count()
        month_logs = logs.filter(prayed_at__date__gte=month_ago).count()

        sessions = PrayerSession.objects.filter(user=user, is_completed=True)
        total_minutes = sum(s.duration_minutes for s in sessions)
        total_sessions = sessions.count()

        journals = PrayerJournal.objects.filter(user=user).count()

        streak_data = {'current_streak': 0, 'longest_streak': 0, 'total_days_prayed': 0}
        try:
            ps = user.prayer_streak
            streak_data = {
                'current_streak': ps.current_streak,
                'longest_streak': ps.longest_streak,
                'total_days_prayed': ps.total_days_prayed,
            }
        except Exception:
            pass

        return Response({
            'success': True,
            'data': {
                'total_prayers': total_prayers,
                'answered': answered,
                'active': active,
                'answer_rate': round(answered / total_prayers * 100, 1) if total_prayers else 0,
                'total_logs': total_logs,
                'week_logs': week_logs,
                'month_logs': month_logs,
                'total_prayer_minutes': total_minutes,
                'total_sessions': total_sessions,
                'journal_entries': journals,
                'streak': streak_data,
            }
        })

class FocusAnalyticsView(APIView):
    """GET /analytics/focus/ - detailed focus mode analytics."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.focus.models import FocusSession
        from datetime import timedelta

        week_ago = timezone.now().date() - timedelta(days=7)
        sessions = FocusSession.objects.filter(user=request.user)
        total = sessions.count()
        completed = sessions.filter(status='completed').count()
        total_minutes = sum(s.duration_minutes for s in sessions.filter(status='completed'))
        total_blocked = sum(s.blocked_attempts for s in sessions.all())
        week_sessions = sessions.filter(started_at__date__gte=week_ago)
        week_minutes = sum(s.duration_minutes for s in week_sessions.filter(status='completed'))

        return Response({
            'success': True,
            'data': {
                'total_sessions': total,
                'completed_sessions': completed,
                'completion_rate': round(completed / total * 100, 1) if total else 0,
                'total_focus_minutes': total_minutes,
                'total_focus_hours': round(total_minutes / 60, 1),
                'total_blocked_attempts': total_blocked,
                'total_time_saved_minutes': total_blocked * 2,
                'this_week_minutes': week_minutes,
            }
        })


class NotesAnalyticsView(APIView):
    """GET /analytics/notes/ - detailed notes analytics."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.notes.models import Note, Folder, Topic
        from datetime import timedelta

        week_ago = timezone.now().date() - timedelta(days=7)
        month_ago = timezone.now().date() - timedelta(days=30)

        notes = Note.objects.filter(user=request.user)
        total = notes.count()
        favorites = notes.filter(is_favorite=True).count()
        archived = notes.filter(is_archived=True).count()
        week_created = notes.filter(created_at__date__gte=week_ago).count()
        month_created = notes.filter(created_at__date__gte=month_ago).count()

        return Response({
            'success': True,
            'data': {
                'total_notes': total,
                'favorites': favorites,
                'archived': archived,
                'week_created': week_created,
                'month_created': month_created,
                'total_folders': Folder.objects.filter(user=request.user).count(),
                'total_topics': Topic.objects.filter(user=request.user).count(),
            }
        })


class ReminderAnalyticsView(APIView):
    """GET /analytics/reminders/ - detailed reminder analytics."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.reminders.models import Reminder

        reminders = Reminder.objects.filter(user=request.user)
        total = reminders.count()
        completed = reminders.filter(status='completed').count()
        pending = reminders.filter(status='pending').count()
        missed = reminders.filter(status='missed').count()
        overdue = sum(1 for r in reminders.filter(status='pending') if r.is_overdue)

        return Response({
            'success': True,
            'data': {
                'total_reminders': total,
                'completed': completed,
                'pending': pending,
                'missed': missed,
                'overdue': overdue,
                'completion_rate': round(completed / total * 100, 1) if total else 0,
            }
        })


class UsageAnalyticsView(APIView):
    """GET /analytics/usage/ - app usage analytics."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.analytics.models import AppUsage
        from datetime import timedelta

        week_ago = timezone.now().date() - timedelta(days=7)
        month_ago = timezone.now().date() - timedelta(days=30)

        usage = AppUsage.objects.filter(user=request.user)
        week_usage = usage.filter(date__gte=week_ago)
        month_usage = usage.filter(date__gte=month_ago)

        return Response({
            'success': True,
            'data': {
                'week_screen_time_seconds': sum(u.screen_time_seconds for u in week_usage),
                'week_screen_time_minutes': sum(u.screen_time_seconds for u in week_usage) // 60,
                'month_screen_time_seconds': sum(u.screen_time_seconds for u in month_usage),
                'month_screen_time_minutes': sum(u.screen_time_seconds for u in month_usage) // 60,
                'total_app_launches': sum(u.session_count for u in usage),
            }
        })


class LogUsageView(APIView):
    """POST /analytics/log-usage/ - log app usage."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from apps.analytics.models import AppUsage

        usage, _ = AppUsage.objects.get_or_create(
            user=request.user,
            date=timezone.now().date(),
            defaults={
                'screen_time_seconds': request.data.get('screen_time_seconds', 0),
                'most_visited_page': request.data.get('most_visited_page', ''),
                'session_count': request.data.get('session_count', 1),
            }
        )
        if not _:
            usage.screen_time_seconds += request.data.get('screen_time_seconds', 0)
            usage.session_count += request.data.get('session_count', 1)
            usage.save()

        return Response({'success': True, 'message': 'Usage logged.'})

