#!/usr/bin/env bash
# Render "Build Command":   ./build.sh
# Render's free tier has no shell, so the Bible is loaded during the build.
# The verse loader DELETES and re-imports each book, which would also remove
# anything pointing at those verses (e.g. verse-of-the-day rows), so it only
# runs when the database has no verses yet.
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate --no-input
python manage.py load_bible_books

if python manage.py shell -c "import sys; from apps.bible.models import BibleVerse; sys.exit(0 if BibleVerse.objects.exists() else 1)"; then
  echo "Bible verses already loaded - skipping import."
else
  python manage.py load_bible_verses
fi
