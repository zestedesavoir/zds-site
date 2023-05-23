from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("utils", "0008_auto_20161112_1757"),
    ]

    operations = [
        migrations.AlterField(
            model_name="alert",
            name="scope",
            field=models.CharField(
                db_index=True,
                max_length=10,
                choices=[(b"FORUM", "Forum"), (b"TUTORIAL", "Tutoriel"), (b"ARTICLE", "Article")],
            ),
        ),
        migrations.RunSQL(
            ("UPDATE utils_alert SET scope='FORUM' WHERE scope='F';"),
            reverse_sql=("UPDATE utils_alert SET scope='F' WHERE scope='FORUM';"),
        ),
        migrations.RunSQL(
            ("UPDATE utils_alert SET scope='ARTICLE' WHERE scope='C';"),
            reverse_sql=("UPDATE utils_alert SET scope='C' WHERE scope='ARTICLE' OR scope='TUTORIAL';"),
        ),
    ]
