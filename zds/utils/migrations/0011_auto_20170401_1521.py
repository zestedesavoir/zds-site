from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tutorialv2", "0020_auto_20170401_1521"),
        ("utils", "0010_auto_20170203_2100"),
    ]

    operations = [
        migrations.AddField(
            model_name="alert",
            name="content",
            field=models.ForeignKey(
                related_name="alerts_on_this_content",
                verbose_name="Contenu",
                blank=True,
                to="tutorialv2.PublishableContent",
                null=True,
                on_delete=models.CASCADE,
            ),
        ),
        migrations.AlterField(
            model_name="alert",
            name="comment",
            field=models.ForeignKey(
                related_name="alerts_on_this_comment",
                verbose_name="Commentaire",
                blank=True,
                to="utils.Comment",
                null=True,
                on_delete=models.CASCADE,
            ),
        ),
        migrations.AlterField(
            model_name="alert",
            name="scope",
            field=models.CharField(
                db_index=True,
                max_length=10,
                choices=[
                    ("FORUM", "Forum"),
                    ("CONTENT", "Contenu"),
                    (b"TUTORIAL", "Tutoriel"),
                    (b"ARTICLE", "Article"),
                    (b"OPINION", "Billet"),
                ],
            ),
        ),
    ]
