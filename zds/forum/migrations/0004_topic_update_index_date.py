from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("forum", "0003_auto_20151110_1145"),
    ]

    operations = [
        migrations.AddField(
            model_name="topic",
            name="update_index_date",
            field=models.DateTimeField(
                default="1000-01-01 00:00:00",
                auto_now=True,
                verbose_name=b"Date de derni\xc3\xa8re modification pour la r\xc3\xa9indexation partielle",
                db_index=True,
            ),
            preserve_default=False,
        ),
    ]
