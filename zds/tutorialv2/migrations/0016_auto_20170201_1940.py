from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tutorialv2", "0015_publishedcontent_nb_letter"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="publishedcontent",
            name="nb_letter",
        ),
        migrations.AddField(
            model_name="publishedcontent",
            name="char_count",
            field=models.IntegerField(
                default=None, null=True, verbose_name=b"Nombre de lettres du contenu", blank=True
            ),
        ),
    ]
