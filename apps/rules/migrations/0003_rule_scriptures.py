from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rules', '0002_alter_rulecategory_options_rulecategory_order_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='rule',
            name='scriptures',
            field=models.JSONField(blank=True, default=list),
        ),
    ]
