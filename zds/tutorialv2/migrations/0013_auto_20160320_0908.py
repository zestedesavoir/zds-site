from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tutorialv2", "0012_publishablecontent_tags"),
    ]

    operations = [
        migrations.AlterField(
            model_name="publishablecontent",
            name="tags",
            field=models.ManyToManyField(to="utils.Tag", db_index=True, verbose_name=b"Tags du contenu", blank=True),
        ),
    ]
