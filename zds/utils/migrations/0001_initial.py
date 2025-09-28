import easy_thumbnails.fields
from django.conf import settings
from django.db import migrations, models

import zds.utils.models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Alert",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                (
                    "scope",
                    models.CharField(
                        db_index=True,
                        max_length=1,
                        choices=[(b"A", b"Commentaire d'article"), (b"F", b"Forum"), (b"T", b"Commentaire de tuto")],
                    ),
                ),
                ("text", models.TextField(verbose_name=b"Texte d'alerte")),
                ("pubdate", models.DateTimeField(verbose_name=b"Date de publication", db_index=True)),
                (
                    "author",
                    models.ForeignKey(
                        related_name="alerts",
                        verbose_name=b"Auteur",
                        to=settings.AUTH_USER_MODEL,
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "verbose_name": "Alerte",
                "verbose_name_plural": "Alertes",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                ("title", models.CharField(max_length=80, verbose_name=b"Titre")),
                ("description", models.TextField(verbose_name=b"Description")),
                ("position", models.IntegerField(default=0, verbose_name=b"Position")),
                ("slug", models.SlugField(max_length=80)),
            ],
            options={
                "verbose_name": "Categorie",
                "verbose_name_plural": "Categories",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="CategorySubCategory",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                (
                    "is_main",
                    models.BooleanField(
                        default=True, db_index=True, verbose_name=b"Est la cat\xc3\xa9gorie principale"
                    ),
                ),
                (
                    "category",
                    models.ForeignKey(verbose_name=b"Cat\xc3\xa9gorie", to="utils.Category", on_delete=models.CASCADE),
                ),
            ],
            options={
                "verbose_name": "Hierarchie cat\xe9gorie",
                "verbose_name_plural": "Hierarchies cat\xe9gories",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Comment",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                ("ip_address", models.CharField(max_length=39, verbose_name=b"Adresse IP de l'auteur ")),
                ("position", models.IntegerField(verbose_name=b"Position", db_index=True)),
                ("text", models.TextField(verbose_name=b"Texte")),
                ("text_html", models.TextField(verbose_name=b"Texte en Html")),
                ("like", models.IntegerField(default=0, verbose_name=b"Likes")),
                ("dislike", models.IntegerField(default=0, verbose_name=b"Dislikes")),
                (
                    "pubdate",
                    models.DateTimeField(auto_now_add=True, verbose_name=b"Date de publication", db_index=True),
                ),
                ("update", models.DateTimeField(null=True, verbose_name=b"Date d'\xc3\xa9dition", blank=True)),
                ("is_visible", models.BooleanField(default=True, verbose_name=b"Est visible")),
                ("text_hidden", models.CharField(default=b"", max_length=80, verbose_name=b"Texte de masquage ")),
                (
                    "author",
                    models.ForeignKey(
                        related_name="comments",
                        verbose_name=b"Auteur",
                        to=settings.AUTH_USER_MODEL,
                        on_delete=models.CASCADE,
                    ),
                ),
                (
                    "editor",
                    models.ForeignKey(
                        related_name="comments-editor",
                        verbose_name=b"Editeur",
                        blank=True,
                        to=settings.AUTH_USER_MODEL,
                        null=True,
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "verbose_name": "Commentaire",
                "verbose_name_plural": "Commentaires",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="CommentDislike",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                ("comments", models.ForeignKey(to="utils.Comment", on_delete=models.CASCADE)),
                (
                    "user",
                    models.ForeignKey(
                        related_name="post_disliked", to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE
                    ),
                ),
            ],
            options={
                "verbose_name": "Ce message est inutile",
                "verbose_name_plural": "Ces messages sont inutiles",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="CommentLike",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                ("comments", models.ForeignKey(to="utils.Comment", on_delete=models.CASCADE)),
                (
                    "user",
                    models.ForeignKey(related_name="post_liked", to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE),
                ),
            ],
            options={
                "verbose_name": "Ce message est utile",
                "verbose_name_plural": "Ces messages sont utiles",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="HelpWriting",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                ("title", models.CharField(max_length=20, verbose_name=b"Name")),
                ("slug", models.SlugField(max_length=20)),
                ("tablelabel", models.CharField(max_length=150, verbose_name=b"TableLabel")),
                ("image", easy_thumbnails.fields.ThumbnailerImageField(upload_to=zds.utils.models.image_path_help)),
            ],
            options={
                "verbose_name": "Aide \xe0 la r\xe9daction",
                "verbose_name_plural": "Aides \xe0 la r\xe9daction",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Licence",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                ("code", models.CharField(max_length=20, verbose_name=b"Code")),
                ("title", models.CharField(max_length=80, verbose_name=b"Titre")),
                ("description", models.TextField(verbose_name=b"Description")),
            ],
            options={
                "verbose_name": "Licence",
                "verbose_name_plural": "Licences",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="SubCategory",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                ("title", models.CharField(max_length=80, verbose_name=b"Titre")),
                ("subtitle", models.CharField(max_length=200, verbose_name=b"Sous-titre")),
                ("image", models.ImageField(null=True, upload_to=zds.utils.models.image_path_category, blank=True)),
                ("slug", models.SlugField(max_length=80)),
            ],
            options={
                "verbose_name": "Sous-categorie",
                "verbose_name_plural": "Sous-categories",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Tag",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                ("title", models.CharField(max_length=20, verbose_name=b"Titre")),
                ("slug", models.SlugField(max_length=20)),
            ],
            options={
                "verbose_name": "Tag",
                "verbose_name_plural": "Tags",
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name="categorysubcategory",
            name="subcategory",
            field=models.ForeignKey(
                verbose_name=b"Sous-Cat\xc3\xa9gorie", to="utils.SubCategory", on_delete=models.CASCADE
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="alert",
            name="comment",
            field=models.ForeignKey(
                related_name="alerts", verbose_name=b"Commentaire", to="utils.Comment", on_delete=models.CASCADE
            ),
            preserve_default=True,
        ),
    ]
