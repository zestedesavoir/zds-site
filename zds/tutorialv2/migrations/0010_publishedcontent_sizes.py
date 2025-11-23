from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tutorialv2", "0009_publishedcontent_authors"),
    ]

    operations = [
        migrations.AddField(
            model_name="publishedcontent",
            name="sizes",
            field=models.CharField(
                default=b"{}", max_length=512, verbose_name=b"Tailles des fichiers t\xc3\xa9l\xc3\xa9chargeables"
            ),
            preserve_default=True,
        ),
    ]
