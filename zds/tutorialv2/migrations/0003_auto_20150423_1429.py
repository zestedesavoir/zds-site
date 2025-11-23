from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tutorialv2", "0002_auto_20150417_0445"),
    ]

    operations = [
        migrations.AlterField(
            model_name="contentread",
            name="note",
            field=models.ForeignKey(to="tutorialv2.ContentReaction", null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="publishedcontent",
            name="sha_public",
            field=models.CharField(
                db_index=True, max_length=80, null=True, verbose_name=b"Sha1 de la version publi\xc3\xa9e", blank=True
            ),
            preserve_default=True,
        ),
    ]
