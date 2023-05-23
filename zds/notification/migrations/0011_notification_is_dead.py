from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("notification", "0010_newpublicationsubscription"),
    ]

    operations = [
        migrations.AddField(
            model_name="notification",
            name="is_dead",
            field=models.BooleanField(default=False, verbose_name="Morte"),
        ),
    ]
