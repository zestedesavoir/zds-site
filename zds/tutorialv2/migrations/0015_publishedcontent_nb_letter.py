from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tutorialv2", "0014_auto_20160331_0415"),
    ]

    operations = [
        migrations.AddField(
            model_name="publishedcontent",
            name="nb_letter",
            field=models.IntegerField(
                default=None, null=True, verbose_name=b"Nombre de caract\xc3\xa8res du contenu", blank=True
            ),
        ),
    ]
