from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("featured", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="featuredmessage",
            name="hook",
            field=models.CharField(max_length=100, null=True, verbose_name="Accroche", blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="featuredresource",
            name="source",
            field=models.CharField(default=b"", max_length=100, verbose_name="Auteurs", blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="featuredmessage",
            name="message",
            field=models.CharField(max_length=255, null=True, verbose_name="Message", blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="featuredmessage",
            name="url",
            field=models.CharField(max_length=2000, null=True, verbose_name="URL du message", blank=True),
            preserve_default=True,
        ),
    ]
