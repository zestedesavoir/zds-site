import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("forum", "0002_auto_20150410_1505"),
        ("gallery", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("utils", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ContentReaction",
            fields=[
                (
                    "comment_ptr",
                    models.OneToOneField(
                        parent_link=True,
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        to="utils.Comment",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "verbose_name": "note sur un contenu",
                "verbose_name_plural": "notes sur un contenu",
            },
            bases=("utils.comment",),
        ),
        migrations.CreateModel(
            name="ContentRead",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
                "verbose_name": "Contenu lu",
                "verbose_name_plural": "Contenu lus",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="PublishableContent",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                ("title", models.CharField(max_length=80, verbose_name=b"Titre")),
                ("slug", models.CharField(max_length=80, verbose_name=b"Slug")),
                ("description", models.CharField(max_length=200, verbose_name=b"Description")),
                ("source", models.CharField(max_length=200, verbose_name=b"Source")),
                ("old_pk", models.IntegerField(default=0, db_index=True)),
                ("creation_date", models.DateTimeField(verbose_name=b"Date de cr\xc3\xa9ation")),
                (
                    "pubdate",
                    models.DateTimeField(db_index=True, null=True, verbose_name=b"Date de publication", blank=True),
                ),
                (
                    "update_date",
                    models.DateTimeField(null=True, verbose_name=b"Date de mise \xc3\xa0 jour", blank=True),
                ),
                (
                    "sha_public",
                    models.CharField(
                        db_index=True, max_length=80, null=True, verbose_name=b"Sha1 de la version publique", blank=True
                    ),
                ),
                (
                    "sha_beta",
                    models.CharField(
                        db_index=True,
                        max_length=80,
                        null=True,
                        verbose_name=b"Sha1 de la version beta publique",
                        blank=True,
                    ),
                ),
                (
                    "sha_validation",
                    models.CharField(
                        db_index=True,
                        max_length=80,
                        null=True,
                        verbose_name=b"Sha1 de la version en validation",
                        blank=True,
                    ),
                ),
                (
                    "sha_draft",
                    models.CharField(
                        db_index=True,
                        max_length=80,
                        null=True,
                        verbose_name=b"Sha1 de la version de r\xc3\xa9daction",
                        blank=True,
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        db_index=True, max_length=10, choices=[(b"TUTORIAL", b"Tutoriel"), (b"ARTICLE", b"Article")]
                    ),
                ),
                (
                    "relative_images_path",
                    models.CharField(max_length=200, null=True, verbose_name=b"chemin relatif images", blank=True),
                ),
                ("is_locked", models.BooleanField(default=False, verbose_name=b"Est verrouill\xc3\xa9")),
                ("js_support", models.BooleanField(default=False, verbose_name=b"Support du Javascript")),
                (
                    "authors",
                    models.ManyToManyField(to=settings.AUTH_USER_MODEL, verbose_name=b"Auteurs", db_index=True),
                ),
                (
                    "beta_topic",
                    models.ForeignKey(
                        default=None,
                        verbose_name=b"Contenu associ\xc3\xa9",
                        to="forum.Topic",
                        null=True,
                        on_delete=models.CASCADE,
                    ),
                ),
                (
                    "gallery",
                    models.ForeignKey(
                        verbose_name=b"Galerie d'images",
                        blank=True,
                        to="gallery.Gallery",
                        null=True,
                        on_delete=models.CASCADE,
                    ),
                ),
                ("helps", models.ManyToManyField(to="utils.HelpWriting", verbose_name=b"Aides", db_index=True)),
                (
                    "image",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.SET_NULL,
                        verbose_name=b"Image du tutoriel",
                        blank=True,
                        to="gallery.Image",
                        null=True,
                    ),
                ),
                (
                    "last_note",
                    models.ForeignKey(
                        related_name="last_note",
                        verbose_name=b"Derniere note",
                        blank=True,
                        to="tutorialv2.ContentReaction",
                        null=True,
                        on_delete=models.CASCADE,
                    ),
                ),
                (
                    "licence",
                    models.ForeignKey(
                        verbose_name=b"Licence", blank=True, to="utils.Licence", null=True, on_delete=models.CASCADE
                    ),
                ),
                (
                    "subcategory",
                    models.ManyToManyField(
                        db_index=True,
                        to="utils.SubCategory",
                        null=True,
                        verbose_name=b"Sous-Cat\xc3\xa9gorie",
                        blank=True,
                    ),
                ),
            ],
            options={
                "verbose_name": "Contenu",
                "verbose_name_plural": "Contenus",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Validation",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                (
                    "version",
                    models.CharField(
                        db_index=True, max_length=80, null=True, verbose_name=b"Sha1 de la version", blank=True
                    ),
                ),
                ("date_proposition", models.DateTimeField(verbose_name=b"Date de proposition", db_index=True)),
                ("comment_authors", models.TextField(verbose_name=b"Commentaire de l'auteur")),
                (
                    "date_reserve",
                    models.DateTimeField(null=True, verbose_name=b"Date de r\xc3\xa9servation", blank=True),
                ),
                ("date_validation", models.DateTimeField(null=True, verbose_name=b"Date de validation", blank=True)),
                (
                    "comment_validator",
                    models.TextField(null=True, verbose_name=b"Commentaire du validateur", blank=True),
                ),
                (
                    "status",
                    models.CharField(
                        default=b"PENDING",
                        max_length=10,
                        choices=[
                            (b"PENDING", b"En attente d'un validateur"),
                            (b"PENDING_V", b"En cours de validation"),
                            (b"ACCEPT", b"Publi\xc3\xa9"),
                            (b"REJECT", b"Rejet\xc3\xa9"),
                        ],
                    ),
                ),
                (
                    "content",
                    models.ForeignKey(
                        verbose_name=b"Contenu propos\xc3\xa9",
                        blank=True,
                        to="tutorialv2.PublishableContent",
                        null=True,
                        on_delete=models.CASCADE,
                    ),
                ),
                (
                    "validator",
                    models.ForeignKey(
                        related_name="author_content_validations",
                        verbose_name=b"Validateur",
                        blank=True,
                        to=settings.AUTH_USER_MODEL,
                        null=True,
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "verbose_name": "Validation",
                "verbose_name_plural": "Validations",
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name="contentread",
            name="content",
            field=models.ForeignKey(to="tutorialv2.PublishableContent", on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="contentread",
            name="note",
            field=models.ForeignKey(to="tutorialv2.ContentReaction", on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="contentread",
            name="user",
            field=models.ForeignKey(
                related_name="content_notes_read", to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="contentreaction",
            name="related_content",
            field=models.ForeignKey(
                related_name="related_content_note",
                verbose_name=b"Contenu",
                to="tutorialv2.PublishableContent",
                on_delete=models.CASCADE,
            ),
            preserve_default=True,
        ),
    ]
