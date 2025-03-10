import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tutorialv2", "0003_auto_20150423_1429"),
    ]

    operations = [
        migrations.AddField(
            model_name="publishablecontent",
            name="public_version",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.SET_NULL,
                verbose_name=b"Version publi\xc3\xa9e",
                blank=True,
                to="tutorialv2.PublishedContent",
                null=True,
            ),
            preserve_default=True,
        ),
    ]
