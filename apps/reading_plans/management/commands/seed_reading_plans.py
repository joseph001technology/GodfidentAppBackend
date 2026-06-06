"""
Management command to seed default reading plans.
Run: python manage.py seed_reading_plans
"""
from django.core.management.base import BaseCommand
from apps.reading_plans.models import ReadingPlan, ReadingPlanDay

# Proverbs 31-day plan: one chapter per day
PROVERBS_PLAN = {
    'name': 'Proverbs in a Month',
    'description': 'Read through all 31 chapters of Proverbs — one chapter per day.',
    'plan_type': 'proverbs',
    'duration_days': 31,
    'days': [
        {'day': i, 'title': f'Proverbs {i}', 'readings': [{'book': 'Proverbs', 'chapter_start': i, 'chapter_end': i}]}
        for i in range(1, 32)
    ]
}

# Gospels plan: Matthew, Mark, Luke, John
GOSPELS_PLAN = {
    'name': 'The Four Gospels',
    'description': 'Read through all four Gospels: Matthew, Mark, Luke, and John.',
    'plan_type': 'gospel',
    'duration_days': 89,
    'days': (
        [{'day': i, 'title': f'Matthew {i}', 'readings': [{'book': 'Matthew', 'chapter_start': i, 'chapter_end': i}]} for i in range(1, 29)] +
        [{'day': 28 + i, 'title': f'Mark {i}', 'readings': [{'book': 'Mark', 'chapter_start': i, 'chapter_end': i}]} for i in range(1, 17)] +
        [{'day': 44 + i, 'title': f'Luke {i}', 'readings': [{'book': 'Luke', 'chapter_start': i, 'chapter_end': i}]} for i in range(1, 25)] +
        [{'day': 68 + i, 'title': f'John {i}', 'readings': [{'book': 'John', 'chapter_start': i, 'chapter_end': i}]} for i in range(1, 22)]
    )
}

# New Testament in 90 days (~3 chapters/day)
NT_90_DAYS = {
    'name': 'New Testament in 90 Days',
    'description': 'Read through the entire New Testament in 90 days (~3 chapters per day).',
    'plan_type': 'nt',
    'duration_days': 90,
    'days': []  # Populated below
}

NT_BOOKS = [
    ('Matthew', 28), ('Mark', 16), ('Luke', 24), ('John', 21),
    ('Acts', 28), ('Romans', 16), ('1 Corinthians', 16), ('2 Corinthians', 13),
    ('Galatians', 6), ('Ephesians', 6), ('Philippians', 4), ('Colossians', 4),
    ('1 Thessalonians', 5), ('2 Thessalonians', 3), ('1 Timothy', 6),
    ('2 Timothy', 4), ('Titus', 3), ('Philemon', 1), ('Hebrews', 13),
    ('James', 5), ('1 Peter', 5), ('2 Peter', 3), ('1 John', 5),
    ('2 John', 1), ('3 John', 1), ('Jude', 1), ('Revelation', 22),
]

# Build NT chapters list
all_nt_chapters = []
for book, chapters in NT_BOOKS:
    for ch in range(1, chapters + 1):
        all_nt_chapters.append((book, ch))

# Group into 90 days (~3 per day)
chunks = [all_nt_chapters[i:i+3] for i in range(0, len(all_nt_chapters), 3)]
for idx, chunk in enumerate(chunks[:90], start=1):
    books_in_chunk = ', '.join(f'{b} {c}' for b, c in chunk)
    NT_90_DAYS['days'].append({
        'day': idx,
        'title': f'Day {idx}: {books_in_chunk}',
        'readings': [{'book': b, 'chapter_start': c, 'chapter_end': c} for b, c in chunk]
    })

PLANS = [PROVERBS_PLAN, GOSPELS_PLAN, NT_90_DAYS]


class Command(BaseCommand):
    help = 'Seed default reading plans'

    def handle(self, *args, **options):
        for plan_data in PLANS:
            plan, created = ReadingPlan.objects.get_or_create(
                name=plan_data['name'],
                defaults={
                    'description': plan_data['description'],
                    'plan_type': plan_data['plan_type'],
                    'duration_days': plan_data['duration_days'],
                }
            )
            if created:
                self.stdout.write(f'Created plan: {plan.name}')
                for day_data in plan_data['days']:
                    ReadingPlanDay.objects.create(
                        plan=plan,
                        day_number=day_data['day'],
                        title=day_data['title'],
                        readings=day_data['readings'],
                    )
                self.stdout.write(f'  Added {len(plan_data["days"])} days')
            else:
                self.stdout.write(f'Plan already exists: {plan.name}')

        self.stdout.write(self.style.SUCCESS('\nReading plans seeded successfully!'))
