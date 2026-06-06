"""
Management command to load the Bible books structure.
Run: python manage.py load_bible_books

After this, you can import actual verse text from a public domain JSON source.
See README for instructions on importing full Bible text.
"""
from django.core.management.base import BaseCommand
from apps.bible.models import BibleBook, BibleTranslation


BOOKS_DATA = [
    # (number, name, abbreviation, testament, chapters)
    (1, 'Genesis', 'Gen', 'OT', 50), (2, 'Exodus', 'Exo', 'OT', 40),
    (3, 'Leviticus', 'Lev', 'OT', 27), (4, 'Numbers', 'Num', 'OT', 36),
    (5, 'Deuteronomy', 'Deu', 'OT', 34), (6, 'Joshua', 'Jos', 'OT', 24),
    (7, 'Judges', 'Jdg', 'OT', 21), (8, 'Ruth', 'Rut', 'OT', 4),
    (9, '1 Samuel', '1Sa', 'OT', 31), (10, '2 Samuel', '2Sa', 'OT', 24),
    (11, '1 Kings', '1Ki', 'OT', 22), (12, '2 Kings', '2Ki', 'OT', 25),
    (13, '1 Chronicles', '1Ch', 'OT', 29), (14, '2 Chronicles', '2Ch', 'OT', 36),
    (15, 'Ezra', 'Ezr', 'OT', 10), (16, 'Nehemiah', 'Neh', 'OT', 13),
    (17, 'Esther', 'Est', 'OT', 10), (18, 'Job', 'Job', 'OT', 42),
    (19, 'Psalms', 'Psa', 'OT', 150), (20, 'Proverbs', 'Pro', 'OT', 31),
    (21, 'Ecclesiastes', 'Ecc', 'OT', 12), (22, 'Song of Solomon', 'Son', 'OT', 8),
    (23, 'Isaiah', 'Isa', 'OT', 66), (24, 'Jeremiah', 'Jer', 'OT', 52),
    (25, 'Lamentations', 'Lam', 'OT', 5), (26, 'Ezekiel', 'Eze', 'OT', 48),
    (27, 'Daniel', 'Dan', 'OT', 12), (28, 'Hosea', 'Hos', 'OT', 14),
    (29, 'Joel', 'Joe', 'OT', 3), (30, 'Amos', 'Amo', 'OT', 9),
    (31, 'Obadiah', 'Oba', 'OT', 1), (32, 'Jonah', 'Jon', 'OT', 4),
    (33, 'Micah', 'Mic', 'OT', 7), (34, 'Nahum', 'Nah', 'OT', 3),
    (35, 'Habakkuk', 'Hab', 'OT', 3), (36, 'Zephaniah', 'Zep', 'OT', 3),
    (37, 'Haggai', 'Hag', 'OT', 2), (38, 'Zechariah', 'Zec', 'OT', 14),
    (39, 'Malachi', 'Mal', 'OT', 4),
    (40, 'Matthew', 'Mat', 'NT', 28), (41, 'Mark', 'Mar', 'NT', 16),
    (42, 'Luke', 'Luk', 'NT', 24), (43, 'John', 'Joh', 'NT', 21),
    (44, 'Acts', 'Act', 'NT', 28), (45, 'Romans', 'Rom', 'NT', 16),
    (46, '1 Corinthians', '1Co', 'NT', 16), (47, '2 Corinthians', '2Co', 'NT', 13),
    (48, 'Galatians', 'Gal', 'NT', 6), (49, 'Ephesians', 'Eph', 'NT', 6),
    (50, 'Philippians', 'Phi', 'NT', 4), (51, 'Colossians', 'Col', 'NT', 4),
    (52, '1 Thessalonians', '1Th', 'NT', 5), (53, '2 Thessalonians', '2Th', 'NT', 3),
    (54, '1 Timothy', '1Ti', 'NT', 6), (55, '2 Timothy', '2Ti', 'NT', 4),
    (56, 'Titus', 'Tit', 'NT', 3), (57, 'Philemon', 'Phm', 'NT', 1),
    (58, 'Hebrews', 'Heb', 'NT', 13), (59, 'James', 'Jam', 'NT', 5),
    (60, '1 Peter', '1Pe', 'NT', 5), (61, '2 Peter', '2Pe', 'NT', 3),
    (62, '1 John', '1Jo', 'NT', 5), (63, '2 John', '2Jo', 'NT', 1),
    (64, '3 John', '3Jo', 'NT', 1), (65, 'Jude', 'Jud', 'NT', 1),
    (66, 'Revelation', 'Rev', 'NT', 22),
]

TRANSLATIONS = [
    ('KJV', 'King James Version', 'King James Version (1611)', 'English'),
    ('NKJV', 'NKJV', 'New King James Version', 'English'),
    ('NIV', 'NIV', 'New International Version', 'English'),
    ('ESV', 'ESV', 'English Standard Version', 'English'),
    ('NLT', 'NLT', 'New Living Translation', 'English'),
]


class Command(BaseCommand):
    help = 'Load Bible books and translations into the database'

    def handle(self, *args, **options):
        self.stdout.write('Loading Bible translations...')
        for code, name, full_name, language in TRANSLATIONS:
            obj, created = BibleTranslation.objects.get_or_create(
                code=code,
                defaults={'name': name, 'full_name': full_name, 'language': language}
            )
            if created:
                self.stdout.write(f'  Created translation: {code}')

        self.stdout.write('Loading Bible books...')
        for number, name, abbreviation, testament, chapter_count in BOOKS_DATA:
            obj, created = BibleBook.objects.get_or_create(
                number=number,
                defaults={
                    'name': name,
                    'abbreviation': abbreviation,
                    'testament': testament,
                    'chapter_count': chapter_count,
                }
            )
            if created:
                self.stdout.write(f'  Created book: {name}')

        self.stdout.write(self.style.SUCCESS(
            '\nDone! Books and translations loaded.\n'
            'Next: Import verse text using load_bible_verses command.\n'
            'See README.md for instructions on downloading public domain Bible text.'
        ))
