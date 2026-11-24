from django.db import migrations, models


class Migration(migrations.Migration):
    """Prayers can now be for someone else: who it is for + a 'mine / other' flag."""

    dependencies = [
        ('prayer', '0004_answered_prayers_thanksgiving'),
    ]

    operations = [
        migrations.AddField(
            model_name='prayer',
            name='prayer_for',
            field=models.CharField(
                choices=[('self', 'My own prayer'), ('other', "Someone else's prayer")],
                db_index=True, default='self', max_length=10,
            ),
        ),
        migrations.AddField(
            model_name='prayer',
            name='person_name',
            field=models.CharField(blank=True, max_length=120),
        ),
    ]
