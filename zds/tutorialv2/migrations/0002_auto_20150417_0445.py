from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tutorialv2", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="PublishedContent",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                (
                    "content_type",
                    models.CharField(
                        db_index=True,
                        max_length=10,
                        verbose_name=b"Type de contenu",
                        choices=[(b"TUTORIAL", b"Tutoriel"), (b"ARTICLE", b"Article")],
                    ),
                ),
                ("content_public_slug", models.CharField(max_length=80, verbose_name=b"Slug du contenu publi\xc3\xa9")),
                ("content_pk", models.IntegerField(verbose_name=b"Pk du contenu publi\xc3\xa9", db_index=True)),
                (
                    "publication_date",
                    models.DateTimeField(db_index=True, null=True, verbose_name=b"Date de publication", blank=True),
                ),
                (
                    "sha_public",
                    models.CharField(
                        db_index=True, max_length=80, null=True, verbose_name=b"Sha1 de la version publique", blank=True
                    ),
                ),
                (
                    "content",
                    models.ForeignKey(
                        verbose_name=b"Contenu", to="tutorialv2.PublishableContent", on_delete=models.CASCADE
                    ),
                ),
            ],
            options={
                "verbose_name": "Contenu publi\xe9",
                "verbose_name_plural": "Contenus publi\xe9s",
            },
            bases=(models.Model,),
        ),
        migrations.AlterField(
            model_name="validation",
            name="comment_authors",
            field=models.TextField(null=True, verbose_name=b"Commentaire de l'auteur", blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="validation",
            name="date_proposition",
            field=models.DateTimeField(db_index=True, null=True, verbose_name=b"Date de proposition", blank=True),
            preserve_default=True,
        ),
    ]
