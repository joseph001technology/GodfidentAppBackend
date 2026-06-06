import factory
from factory.django import DjangoModelFactory
from django.utils import timezone
from datetime import timedelta


class UserFactory(DjangoModelFactory):
    class Meta:
        model = 'accounts.User'

    email = factory.Sequence(lambda n: f'user{n}@test.com')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    password = factory.PostGenerationMethodCall('set_password', 'TestPass123!')
    is_email_verified = True


class UserProfileFactory(DjangoModelFactory):
    class Meta:
        model = 'accounts.UserProfile'

    user = factory.SubFactory(UserFactory)
    preferred_translation = 'KJV'


class BibleTranslationFactory(DjangoModelFactory):
    class Meta:
        model = 'bible.BibleTranslation'
        django_get_or_create = ['code']

    code = 'KJV'
    name = 'King James Version'
    full_name = 'King James Version (1611)'
    language = 'English'


class BibleBookFactory(DjangoModelFactory):
    class Meta:
        model = 'bible.BibleBook'
        django_get_or_create = ['number']

    number = factory.Sequence(lambda n: n + 1)
    name = factory.Sequence(lambda n: f'Book{n}')
    abbreviation = factory.Sequence(lambda n: f'B{n}')
    testament = 'NT'
    chapter_count = 21


class BibleVerseFactory(DjangoModelFactory):
    class Meta:
        model = 'bible.BibleVerse'

    translation = factory.SubFactory(BibleTranslationFactory)
    book = factory.SubFactory(BibleBookFactory)
    chapter = 3
    verse = 16
    text = 'For God so loved the world...'


class DevotionalCategoryFactory(DjangoModelFactory):
    class Meta:
        model = 'devotionals.DevotionalCategory'

    name = factory.Sequence(lambda n: f'Category {n}')


class DevotionalFactory(DjangoModelFactory):
    class Meta:
        model = 'devotionals.Devotional'

    title = factory.Faker('sentence', nb_words=5)
    scripture_reference = 'John 3:16'
    scripture_text = 'For God so loved the world...'
    reflection = factory.Faker('paragraph')
    prayer = factory.Faker('paragraph')
    application = factory.Faker('paragraph')
    key_takeaway = factory.Faker('sentence')
    is_published = True
    category = factory.SubFactory(DevotionalCategoryFactory)


class PrayerFactory(DjangoModelFactory):
    class Meta:
        model = 'prayer.Prayer'

    user = factory.SubFactory(UserFactory)
    title = factory.Faker('sentence', nb_words=4)
    content = factory.Faker('paragraph')
    prayer_type = 'request'
    status = 'active'


class ReadingPlanFactory(DjangoModelFactory):
    class Meta:
        model = 'reading_plans.ReadingPlan'

    name = factory.Sequence(lambda n: f'Reading Plan {n}')
    description = factory.Faker('paragraph')
    plan_type = 'canonical'
    duration_days = 30
    is_active = True
