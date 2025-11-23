from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("mp", "0002_auto_20150416_1750"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("utils", "0007_auto_20160511_2153"),
    ]

    operations = [
        migrations.AddField(
            model_name="alert",
            name="moderator",
            field=models.ForeignKey(
                related_name="solved_alerts",
                verbose_name=b"Mod\xc3\xa9rateur",
                blank=True,
                to=settings.AUTH_USER_MODEL,
                null=True,
                on_delete=models.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="alert",
            name="privatetopic",
            field=models.ForeignKey(
                verbose_name="Message priv\xe9", blank=True, to="mp.PrivateTopic", null=True, on_delete=models.CASCADE
            ),
        ),
        migrations.AddField(
            model_name="alert",
            name="resolve_reason",
            field=models.TextField(null=True, verbose_name=b"Texte de r\xc3\xa9solution", blank=True),
        ),
        migrations.AddField(
            model_name="alert",
            name="solved",
            field=models.BooleanField(default=False, verbose_name=b"Est r\xc3\xa9solue"),
        ),
        migrations.AddField(
            model_name="alert",
            name="solved_date",
            field=models.DateTimeField(db_index=True, null=True, verbose_name=b"Date de r\xc3\xa9solution", blank=True),
        ),
        migrations.AlterField(
            model_name="alert",
            name="pubdate",
            field=models.DateTimeField(verbose_name=b"Date de cr\xc3\xa9ation", db_index=True),
        ),
    ]
