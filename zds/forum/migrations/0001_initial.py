from django.conf import settings
from django.db import migrations, models

import zds.forum.models


class Migration(migrations.Migration):
    dependencies = [
        ("utils", "0001_initial"),
        ("auth", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                ("title", models.CharField(max_length=80, verbose_name=b"Titre")),
                ("position", models.IntegerField(null=True, verbose_name=b"Position", blank=True)),
                (
                    "slug",
                    models.SlugField(
                        help_text=b"Ces slugs vont provoquer des conflits d'URL et sont donc interdits : notifications resolution_alerte sujet sujets message messages",
                        unique=True,
                        max_length=80,
                    ),
                ),
            ],
            options={
                "verbose_name": "Cat\xe9gorie",
                "verbose_name_plural": "Cat\xe9gories",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Forum",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                ("title", models.CharField(max_length=80, verbose_name=b"Titre")),
                ("subtitle", models.CharField(max_length=200, verbose_name=b"Sous-titre")),
                ("image", models.ImageField(upload_to="forum/normal")),
                (
                    "position_in_category",
                    models.IntegerField(
                        db_index=True, null=True, verbose_name=b"Position dans la cat\xc3\xa9gorie", blank=True
                    ),
                ),
                ("slug", models.SlugField(unique=True, max_length=80)),
                (
                    "category",
                    models.ForeignKey(verbose_name=b"Cat\xc3\xa9gorie", to="forum.Category", on_delete=models.CASCADE),
                ),
                (
                    "group",
                    models.ManyToManyField(
                        to="auth.Group", null=True, verbose_name=b"Groupe autoris\xc3\xa9s (Aucun = public)", blank=True
                    ),
                ),
            ],
            options={
                "verbose_name": "Forum",
                "verbose_name_plural": "Forums",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Post",
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
                ("is_useful", models.BooleanField(default=False, verbose_name=b"Est utile")),
            ],
            options={},
            bases=("utils.comment",),
        ),
        migrations.CreateModel(
            name="Topic",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                ("title", models.CharField(max_length=80, verbose_name=b"Titre")),
                ("subtitle", models.CharField(max_length=200, verbose_name=b"Sous-titre")),
                ("pubdate", models.DateTimeField(auto_now_add=True, verbose_name=b"Date de cr\xc3\xa9ation")),
                ("is_solved", models.BooleanField(default=False, db_index=True, verbose_name=b"Est r\xc3\xa9solu")),
                ("is_locked", models.BooleanField(default=False, verbose_name=b"Est verrouill\xc3\xa9")),
                ("is_sticky", models.BooleanField(default=False, db_index=True, verbose_name=b"Est en post-it")),
                ("key", models.IntegerField(null=True, verbose_name=b"cle", blank=True)),
                (
                    "author",
                    models.ForeignKey(
                        related_name="topics",
                        verbose_name=b"Auteur",
                        to=settings.AUTH_USER_MODEL,
                        on_delete=models.CASCADE,
                    ),
                ),
                ("forum", models.ForeignKey(verbose_name=b"Forum", to="forum.Forum", on_delete=models.CASCADE)),
                (
                    "last_message",
                    models.ForeignKey(
                        related_name="last_message",
                        verbose_name=b"Dernier message",
                        to="forum.Post",
                        null=True,
                        on_delete=models.CASCADE,
                    ),
                ),
                (
                    "tags",
                    models.ManyToManyField(
                        db_index=True, to="utils.Tag", null=True, verbose_name=b"Tags du forum", blank=True
                    ),
                ),
            ],
            options={
                "verbose_name": "Sujet",
                "verbose_name_plural": "Sujets",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="TopicFollowed",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                ("email", models.BooleanField(default=False, db_index=True, verbose_name=b"Notification par courriel")),
                ("topic", models.ForeignKey(to="forum.Topic", on_delete=models.CASCADE)),
                (
                    "user",
                    models.ForeignKey(
                        related_name="topics_followed", to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE
                    ),
                ),
            ],
            options={
                "verbose_name": "Sujet suivi",
                "verbose_name_plural": "Sujets suivis",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="TopicRead",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                ("post", models.ForeignKey(to="forum.Post", on_delete=models.CASCADE)),
                ("topic", models.ForeignKey(to="forum.Topic", on_delete=models.CASCADE)),
                (
                    "user",
                    models.ForeignKey(
                        related_name="topics_read", to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE
                    ),
                ),
            ],
            options={
                "verbose_name": "Sujet lu",
                "verbose_name_plural": "Sujets lus",
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name="post",
            name="topic",
            field=models.ForeignKey(verbose_name=b"Sujet", to="forum.Topic", on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
