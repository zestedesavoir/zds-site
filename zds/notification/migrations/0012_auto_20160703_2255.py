from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("notification", "0011_notification_is_dead"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="subscription",
            unique_together={("user", "content_type", "object_id")},
        ),
    ]
