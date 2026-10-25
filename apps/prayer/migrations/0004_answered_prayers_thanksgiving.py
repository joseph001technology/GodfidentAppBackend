from django.db import migrations


def answered_to_thanksgiving(apps, schema_editor):
    Prayer = apps.get_model('prayer', 'Prayer')
    Prayer.objects.filter(status='answered').exclude(prayer_type='thanksgiving').update(prayer_type='thanksgiving')


class Migration(migrations.Migration):
    """Prayers that were already answered become thanksgiving prayers too."""

    dependencies = [
        ('prayer', '0003_prayersession_planned_minutes'),
    ]

    operations = [
        migrations.RunPython(answered_to_thanksgiving, migrations.RunPython.noop),
    ]
