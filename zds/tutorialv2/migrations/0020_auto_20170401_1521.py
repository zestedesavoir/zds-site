import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tutorialv2", "0019_auto_20170208_1347"),
    ]

    operations = [
        migrations.AddField(
            model_name="publishablecontent",
            name="converted_to",
            field=models.ForeignKey(
                related_name="converted_from",
                on_delete=django.db.models.deletion.SET_NULL,
                verbose_name="Contenu promu",
                blank=True,
                to="tutorialv2.PublishableContent",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="publishablecontent",
            name="picked_date",
            field=models.DateTimeField(
                default=None, null=True, verbose_name="Date de mise en avant", db_index=True, blank=True
            ),
        ),
        migrations.AddField(
            model_name="publishablecontent",
            name="sha_picked",
            field=models.CharField(
                db_index=True,
                max_length=80,
                null=True,
                verbose_name="Sha1 de la version choisie (contenus publi\xe9s sans validation)",
                blank=True,
            ),
        ),
        migrations.AlterField(
            model_name="publishablecontent",
            name="type",
            field=models.CharField(
                db_index=True,
                max_length=10,
                choices=[(b"TUTORIAL", "Tutoriel"), (b"ARTICLE", "Article"), (b"OPINION", "Billet")],
            ),
        ),
        migrations.AlterField(
            model_name="publishedcontent",
            name="content_type",
            field=models.CharField(
                db_index=True,
                max_length=10,
                verbose_name="Type de contenu",
                choices=[(b"TUTORIAL", "Tutoriel"), (b"ARTICLE", "Article"), (b"OPINION", "Billet")],
            ),
        ),
    ]
