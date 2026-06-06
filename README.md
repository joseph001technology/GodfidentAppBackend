# Godfident — Personal Bible Study Platform

A production-ready Django REST Framework backend for personal Bible study, prayer, devotionals, AI Bible assistance, and spiritual growth tracking.

---

## Features

| Feature | Status |
|---|---|
| JWT Authentication (register, login, refresh) | ✅ |
| Email Verification | ✅ |
| Password Reset via email | ✅ |
| API Rate Limiting | ✅ |
| Security Audit Logging | ✅ |
| Bible — 5 Translations (KJV, NKJV, NIV, ESV, NLT) | ✅ |
| Bible — Verse & Chapter Reading | ✅ |
| Bible — Parallel Translation View | ✅ |
| Bible — Search | ✅ |
| Bible — Cross References | ✅ |
| Bookmarks | ✅ |
| Highlights (colour-coded) | ✅ |
| Verse Notes | ✅ |
| Reading Plans (Proverbs, Gospels, NT-90) | ✅ |
| Reading Progress & Streak Tracking | ✅ |
| Daily Devotionals | ✅ |
| Prayer Management (requests, praises, intercession) | ✅ |
| Prayer Logging & Answered Prayer | ✅ |
| AI Chat (Claude-powered, Bible-focused) | ✅ |
| AI — Explain Verse | ✅ |
| AI — Explain Chapter | ✅ |
| AI — Topic Study | ✅ |
| AI — Character Study | ✅ |
| AI — Daily Encouragement | ✅ |
| AI — Prayer Assistance | ✅ |
| Notifications | ✅ |
| Analytics Dashboard | ✅ |
| Reading Heatmap | ✅ |
| Weekly & Monthly Reports | ✅ |
| Swagger / OpenAPI Docs | ✅ |
| Django Admin | ✅ |

---

## Project Structure

```
godfident/
├── godfident/              # Django project settings, urls, exceptions
│   ├── settings.py
│   ├── urls.py
│   ├── exceptions.py       # Standardized error responses
│   └── wsgi.py
├── apps/
│   ├── accounts/           # Custom User, email verification, password reset
│   ├── bible/              # Translations, books, verses, bookmarks, highlights
│   ├── devotionals/        # Daily devotionals, categories, saving
│   ├── reading_plans/      # Plans, progress, streaks
│   ├── prayer/             # Prayer requests, logging, answered prayers
│   ├── ai_assistant/       # Claude AI chat and study tools
│   ├── notifications/      # In-app notifications
│   └── analytics/          # Dashboard, heatmap, weekly/monthly reports
├── tests/                  # All tests
│   ├── factories.py
│   ├── test_accounts.py
│   ├── test_bible.py
│   ├── test_prayer_devotionals.py
│   ├── test_reading_plans.py
│   └── test_analytics_notifications.py
├── requirements.txt
├── .env.example
├── manage.py
└── pytest.ini
```

---

## Setup

### 1. Clone / copy this project

```bash
cd your-projects-folder
# copy this godfident folder here
```

### 2. Create virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Mac/Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your values:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ANTHROPIC_API_KEY=your-anthropic-key

# For email (use console backend for dev):
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### 5. Run migrations

```bash
python manage.py migrate
```

### 6. Load Bible structure (books + translations)

```bash
python manage.py load_bible_books
```

### 7. Import Bible verse text

The Bible text (KJV and others) is public domain but too large to bundle. Import it using:

```bash
# Download public domain KJV JSON:
# https://github.com/aruljohn/Bible-kjv  (JSON format)

# Then load with the import script:
python manage.py load_bible_verses --file kjv.json --translation KJV
```

> **Note:** A `load_bible_verses` command is not included here because Bible JSON formats vary.
> See the section below for writing it, or use the Django admin to import verses.

### 8. Seed reading plans

```bash
python manage.py seed_reading_plans
```

### 9. Create superuser

```bash
python manage.py createsuperuser
```

### 10. Run the server

```bash
python manage.py runserver
```

Visit:
- API: http://127.0.0.1:8000/api/
- Admin: http://127.0.0.1:8000/admin/
- Docs: http://127.0.0.1:8000/api/docs/

---

## Loading Bible Verses

Write `apps/bible/management/commands/load_bible_verses.py`:

```python
import json
from django.core.management.base import BaseCommand
from apps.bible.models import BibleTranslation, BibleBook, BibleVerse

class Command(BaseCommand):
    help = 'Load Bible verses from a JSON file'

    def add_arguments(self, parser):
        parser.add_argument('--file', required=True, help='Path to JSON file')
        parser.add_argument('--translation', required=True, help='Translation code e.g. KJV')

    def handle(self, *args, **options):
        translation = BibleTranslation.objects.get(code=options['translation'])

        with open(options['file']) as f:
            data = json.load(f)

        # Adapt this to your JSON structure
        for book_data in data:
            book = BibleBook.objects.get(name=book_data['name'])
            for chapter_num, verses in enumerate(book_data['chapters'], start=1):
                for verse_num, text in enumerate(verses, start=1):
                    BibleVerse.objects.get_or_create(
                        translation=translation, book=book,
                        chapter=chapter_num, verse=verse_num,
                        defaults={'text': text}
                    )
        self.stdout.write('Done!')
```

**Public domain Bible text sources:**
- KJV: https://github.com/aruljohn/Bible-kjv
- Multiple translations (API): https://scripture.api.bible (free tier)

---

## Running Tests

```bash
# All tests
pytest

# With coverage
coverage run -m pytest && coverage report

# Specific file
pytest tests/test_accounts.py -v
```

---

## API Endpoints Reference

### Auth
| Method | URL | Description |
|---|---|---|
| POST | `/api/auth/register/` | Register |
| POST | `/api/auth/login/` | Login (returns JWT) |
| POST | `/api/auth/token/refresh/` | Refresh access token |
| POST | `/api/auth/verify-email/` | Verify email with token |
| POST | `/api/auth/resend-verification/` | Resend verification email |
| POST | `/api/auth/forgot-password/` | Request password reset |
| POST | `/api/auth/reset-password/` | Reset with token |
| GET/PATCH | `/api/auth/me/` | Get/update user |
| GET/PATCH | `/api/auth/profile/` | Get/update profile |
| POST | `/api/auth/change-password/` | Change password |

### Bible
| Method | URL | Description |
|---|---|---|
| GET | `/api/bible/translations/` | List translations |
| GET | `/api/bible/books/` | List all books |
| GET | `/api/bible/verse/?translation=KJV&book=John&chapter=3&verse=16` | Get verse |
| GET | `/api/bible/chapter/?translation=KJV&book=John&chapter=3` | Get chapter |
| GET | `/api/bible/parallel/?book=John&chapter=3&verse=16&translations=KJV,NIV` | Side-by-side |
| GET | `/api/bible/search/?q=love&translation=KJV` | Search |
| GET | `/api/bible/cross-references/?book=John&chapter=3&verse=16` | Cross refs |
| CRUD | `/api/bible/bookmarks/` | Manage bookmarks |
| CRUD | `/api/bible/highlights/` | Manage highlights |
| CRUD | `/api/bible/notes/` | Manage verse notes |

### Devotionals
| Method | URL | Description |
|---|---|---|
| GET | `/api/devotionals/today/` | Today's devotional |
| GET | `/api/devotionals/` | List all devotionals |
| GET | `/api/devotionals/{id}/` | Get & mark as read |
| POST | `/api/devotionals/{id}/save/` | Save devotional |
| DELETE | `/api/devotionals/{id}/unsave/` | Remove saved |
| GET | `/api/devotionals/saved/` | Saved devotionals |

### Reading Plans
| Method | URL | Description |
|---|---|---|
| GET | `/api/reading-plans/plans/` | List plans |
| GET | `/api/reading-plans/plans/{id}/days/` | Get plan days |
| POST | `/api/reading-plans/my-plans/` | Enroll in plan |
| GET | `/api/reading-plans/my-plans/` | My plans |
| POST | `/api/reading-plans/my-plans/{id}/complete_day/` | Mark day done |
| POST | `/api/reading-plans/my-plans/{id}/pause/` | Pause |
| POST | `/api/reading-plans/my-plans/{id}/resume/` | Resume |
| GET | `/api/reading-plans/streak/` | Reading streak |

### Prayer
| Method | URL | Description |
|---|---|---|
| CRUD | `/api/prayer/` | Manage prayers |
| POST | `/api/prayer/{id}/mark_answered/` | Mark answered |
| POST | `/api/prayer/{id}/log_prayer/` | Log praying |
| GET | `/api/prayer/stats/` | Prayer stats |

### AI Assistant
| Method | URL | Description |
|---|---|---|
| POST | `/api/ai/chat/` | General Bible chat |
| POST | `/api/ai/explain-verse/` | Explain a verse |
| POST | `/api/ai/explain-chapter/` | Study a chapter |
| POST | `/api/ai/topic-study/` | Research a topic |
| POST | `/api/ai/character-study/` | Study a character |
| GET | `/api/ai/daily-encouragement/` | Daily encouragement |
| POST | `/api/ai/prayer-assistance/` | Help with prayer |
| GET | `/api/ai/study-history/` | Past study sessions |

### Analytics
| Method | URL | Description |
|---|---|---|
| GET | `/api/analytics/dashboard/` | Full dashboard |
| GET | `/api/analytics/heatmap/` | Reading heatmap |
| GET | `/api/analytics/weekly/` | This week's stats |
| GET | `/api/analytics/monthly/` | Monthly report |
| POST | `/api/analytics/log-reading/` | Log chapter read |

### Notifications
| Method | URL | Description |
|---|---|---|
| GET | `/api/notifications/` | List notifications |
| GET | `/api/notifications/?unread=true` | Unread only |
| POST | `/api/notifications/{id}/mark_read/` | Mark read |
| POST | `/api/notifications/mark_all_read/` | Mark all read |
| GET | `/api/notifications/unread_count/` | Unread count |

---

## Standardized Response Format

All endpoints follow this format:

```json
{
  "success": true,
  "data": { ... }
}
```

Errors:
```json
{
  "success": false,
  "error_code": "VALIDATION_ERROR",
  "message": "Human-readable message",
  "errors": { ... }
}
```

---

## Tech Stack

- **Django 5.0** + **Django REST Framework 3.15**
- **JWT** via `djangorestframework-simplejwt`
- **AI** via `anthropic` (Claude)
- **Docs** via `drf-spectacular` (Swagger UI)
- **Testing** via `pytest-django` + `factory-boy`
- **Database** SQLite (dev) — swap for PostgreSQL in production

---

## Moving to Production

1. Set `DEBUG=False` and a strong `SECRET_KEY`
2. Switch to PostgreSQL: `DATABASE_URL=postgres://...`
3. Set up real SMTP email
4. Use `gunicorn` + `nginx`
5. Set `ALLOWED_HOSTS` to your domain
6. Run `python manage.py collectstatic`
# GodfidentAppBackend
