from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('focus', '0002_websiteprotectionkey'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='focusschedule',
            options={'ordering': ['start_time', 'id']},
        ),
        migrations.AddField(
            model_name='focusschedule',
            name='title',
            field=models.CharField(blank=True, default='', max_length=120),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='focusschedule',
            name='purpose',
            field=models.CharField(
                choices=[('bible', 'Bible reading'), ('prayer', 'Prayer'), ('both', 'Bible + prayer')],
                default='both', max_length=10),
        ),
        migrations.AddField(
            model_name='focusschedule',
            name='days',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='focusschedule',
            name='once_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='focusschedule',
            name='duration_minutes',
            field=models.PositiveIntegerField(default=30),
        ),
        migrations.AddField(
            model_name='focusschedule',
            name='ringtone',
            field=models.CharField(blank=True, default='', max_length=300),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='focusschedule',
            name='day_of_week',
            field=models.IntegerField(
                blank=True, null=True,
                choices=[(0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), (3, 'Thursday'),
                         (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday')]),
        ),
        migrations.AlterField(
            model_name='focusschedule',
            name='end_time',
            field=models.TimeField(blank=True, null=True),
        ),
    ]
