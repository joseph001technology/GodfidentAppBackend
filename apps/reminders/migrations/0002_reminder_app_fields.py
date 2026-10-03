from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reminders', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='reminder',
            name='is_enabled',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='reminder',
            name='is_alarm',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='reminder',
            name='snooze_minutes',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='reminder',
            name='target_page',
            field=models.CharField(blank=True, default='general', max_length=30),
        ),
    ]
