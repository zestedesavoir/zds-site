from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("utils", "0001_initial"),
        ("tutorialv2", "0011_auto_20160106_2231"),
    ]

    operations = [
        migrations.AddField(
            model_name="publishablecontent",
            name="tags",
            field=models.ManyToManyField(
                db_index=True, to="utils.Tag", null=True, verbose_name=b"Tags du contenu", blank=True
            ),
            preserve_default=True,
        ),
    ]
