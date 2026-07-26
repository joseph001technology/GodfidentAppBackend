"""Services for the Achievements app."""

from .models import Achievement, UserAchievement


def get_user_achievements_summary(user):
    """Get summary of user's achievements."""
    user_achievements = UserAchievement.objects.filter(user=user).select_related('achievement')
    total = Achievement.objects.filter(is_active=True).count()
    unlocked = user_achievements.filter(is_unlocked=True).count()

    # Group by category
    categories = {}
    for ua in user_achievements:
        cat = ua.achievement.category
        if cat not in categories:
            categories[cat] = {'total': 0, 'unlocked': 0, 'achievements': []}
        categories[cat]['total'] += 1
        if ua.is_unlocked:
            categories[cat]['unlocked'] += 1
        categories[cat]['achievements'].append({
            'id': ua.id,
            'code': ua.achievement.code,
            'title': ua.achievement.title,
            'is_unlocked': ua.is_unlocked,
            'progress_percent': ua.progress_percent,
            'unlocked_at': ua.unlocked_at,
        })

    return {
        'total_achievements': total,
        'unlocked': unlocked,
        'locked': total - unlocked,
        'completion_percent': round((unlocked / total * 100), 1) if total else 0,
        'categories': categories,
    }


def seed_achievements():
    """Seed predefined achievements into the database."""
    achievements = [
        # Prayer achievements
        {'code': 'prayer_7_streak', 'title': '7-Day Prayer Streak', 'description': 'Pray for 7 consecutive days.',
         'category': 'prayer', 'icon': 'prayer', 'trigger_event': 'prayer_logged', 'threshold_value': 7, 'order': 1},
        {'code': 'prayer_30_streak', 'title': '30-Day Prayer Streak', 'description': 'Pray for 30 consecutive days.',
         'category': 'prayer', 'icon': 'prayer', 'trigger_event': 'prayer_logged', 'threshold_value': 30, 'order': 2},
        {'code': 'prayer_answered', 'title': 'Answered Prayer', 'description': 'Mark your first prayer as answered.',
         'category': 'prayer', 'icon': 'prayer', 'trigger_event': 'prayer_answered', 'threshold_value': 1, 'order': 3},

        # Reading achievements
        {'code': 'genesis_complete', 'title': 'Genesis Completed', 'description': 'Read all 50 chapters of Genesis.',
         'category': 'reading', 'icon': 'bible', 'trigger_event': 'chapter_read', 'threshold_value': 50, 'order': 4},
        {'code': 'nt_complete', 'title': 'New Testament Completed', 'description': 'Read all 260 NT chapters.',
         'category': 'reading', 'icon': 'bible', 'trigger_event': 'chapter_read', 'threshold_value': 260, 'order': 5},
        {'code': 'psalms_complete', 'title': 'Book of Psalms', 'description': 'Read all 150 Psalms.',
         'category': 'reading', 'icon': 'music', 'trigger_event': 'chapter_read', 'threshold_value': 150, 'order': 6},

        # Notes achievements
        {'code': 'notes_10', 'title': '10 Notes', 'description': 'Create 10 notes.',
         'category': 'notes', 'icon': 'note', 'trigger_event': 'note_created', 'threshold_value': 10, 'order': 7},
        {'code': 'notes_100', 'title': '100 Notes', 'description': 'Create 100 notes.',
         'category': 'notes', 'icon': 'note', 'trigger_event': 'note_created', 'threshold_value': 100, 'order': 8},

        # Bible milestones
        {'code': 'verses_100', 'title': '100 Verses', 'description': 'Read 100 Bible verses.',
         'category': 'milestone', 'icon': 'bible', 'trigger_event': 'verse_read', 'threshold_value': 100, 'order': 9},
        {'code': 'verses_1000', 'title': '1,000 Verses', 'description': 'Read 1,000 Bible verses.',
         'category': 'milestone', 'icon': 'bible', 'trigger_event': 'verse_read', 'threshold_value': 1000, 'order': 10},

        # Streak achievements
        {'code': 'streak_7', 'title': '7-Day Devotion', 'description': 'Use Godfident for 7 consecutive days.',
         'category': 'streak', 'icon': 'fire', 'trigger_event': 'daily_active', 'threshold_value': 7, 'order': 11},
        {'code': 'streak_30', 'title': '30-Day Devotion', 'description': 'Use Godfident for 30 consecutive days.',
         'category': 'streak', 'icon': 'fire', 'trigger_event': 'daily_active', 'threshold_value': 30, 'order': 12},
        {'code': 'streak_365', 'title': '365-Day Devotion', 'description': 'Use Godfident for a full year!',
         'category': 'streak', 'icon': 'crown', 'trigger_event': 'daily_active', 'threshold_value': 365, 'order': 13},

        # Focus achievements
        {'code': 'focus_1', 'title': 'First Focus Session', 'description': 'Complete your first focus session.',
         'category': 'focus', 'icon': 'focus', 'trigger_event': 'focus_completed', 'threshold_value': 1, 'order': 14},
        {'code': 'focus_10', 'title': '10 Focus Sessions', 'description': 'Complete 10 focus sessions.',
         'category': 'focus', 'icon': 'focus', 'trigger_event': 'focus_completed', 'threshold_value': 10, 'order': 15},

        # Devotional achievements
        {'code': 'devotional_7', 'title': '7 Devotionals', 'description': 'Read 7 devotionals.',
         'category': 'devotional', 'icon': 'devotional', 'trigger_event': 'devotional_read', 'threshold_value': 7, 'order': 16},
        {'code': 'devotional_30', 'title': '30 Devotionals', 'description': 'Read 30 devotionals.',
         'category': 'devotional', 'icon': 'devotional', 'trigger_event': 'devotional_read', 'threshold_value': 30, 'order': 17},
    ]

    for data in achievements:
        Achievement.objects.get_or_create(
            code=data['code'],
            defaults=data,
        )
    return len(achievements)
