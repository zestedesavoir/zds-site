from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PrivatePost",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                ("text", models.TextField(verbose_name="Texte")),
                ("text_html", models.TextField(verbose_name="Texte en HTML")),
                ("pubdate", models.DateTimeField(auto_now_add=True, verbose_name="Date de publication", db_index=True)),
                ("update", models.DateTimeField(null=True, verbose_name="Date d'\xe9dition", blank=True)),
                ("position_in_topic", models.IntegerField(verbose_name="Position dans le sujet", db_index=True)),
                (
                    "author",
                    models.ForeignKey(
                        related_name="privateposts",
                        verbose_name=b"Auteur",
                        to=settings.AUTH_USER_MODEL,
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "verbose_name": "R\xe9ponse \xe0 un message priv\xe9",
                "verbose_name_plural": "R\xe9ponses \xe0 un message priv\xe9",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="PrivateTopic",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                ("title", models.CharField(max_length=130, verbose_name="Titre")),
                ("subtitle", models.CharField(max_length=200, verbose_name="Sous-titre")),
                ("pubdate", models.DateTimeField(auto_now_add=True, verbose_name="Date de cr\xe9ation", db_index=True)),
                (
                    "author",
                    models.ForeignKey(
                        related_name="author",
                        verbose_name="Auteur",
                        to=settings.AUTH_USER_MODEL,
                        on_delete=models.CASCADE,
                    ),
                ),
                (
                    "last_message",
                    models.ForeignKey(
                        related_name="last_message",
                        verbose_name="Dernier message",
                        to="mp.PrivatePost",
                        null=True,
                        on_delete=models.CASCADE,
                    ),
                ),
                (
                    "participants",
                    models.ManyToManyField(
                        related_name="participants",
                        verbose_name="Participants",
                        to=settings.AUTH_USER_MODEL,
                        db_index=True,
                    ),
                ),
            ],
            options={
                "verbose_name": "Message priv\xe9",
                "verbose_name_plural": "Messages priv\xe9s",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="PrivateTopicRead",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                ("privatepost", models.ForeignKey(to="mp.PrivatePost", on_delete=models.CASCADE)),
                ("privatetopic", models.ForeignKey(to="mp.PrivateTopic", on_delete=models.CASCADE)),
                (
                    "user",
                    models.ForeignKey(
                        related_name="privatetopics_read", to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE
                    ),
                ),
            ],
            options={
                "verbose_name": "Message priv\xe9 lu",
                "verbose_name_plural": "Messages priv\xe9s lus",
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name="privatepost",
            name="privatetopic",
            field=models.ForeignKey(verbose_name="Message priv\xe9", to="mp.PrivateTopic", on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
