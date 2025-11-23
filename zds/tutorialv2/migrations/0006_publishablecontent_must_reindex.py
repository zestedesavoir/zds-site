from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tutorialv2", "0005_auto_20150510_2114"),
    ]

    operations = [
        migrations.AddField(
            model_name="publishablecontent",
            name="must_reindex",
            field=models.BooleanField(default=True, verbose_name=b"Si le contenu doit-\xc3\xaatre r\xc3\xa9-indexe"),
            preserve_default=True,
        ),
    ]
