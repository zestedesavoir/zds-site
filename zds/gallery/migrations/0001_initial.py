import easy_thumbnails.fields
from django.conf import settings
from django.db import migrations, models

import zds.gallery.models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Gallery",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                ("title", models.CharField(max_length=80, verbose_name=b"Titre")),
                ("subtitle", models.CharField(max_length=200, verbose_name=b"Sous titre")),
                ("slug", models.SlugField(max_length=80)),
                (
                    "pubdate",
                    models.DateTimeField(auto_now_add=True, verbose_name=b"Date de cr\xc3\xa9ation", db_index=True),
                ),
                ("update", models.DateTimeField(null=True, verbose_name=b"Date de modification", blank=True)),
            ],
            options={
                "verbose_name": "Galerie",
                "verbose_name_plural": "Galeries",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Image",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                ("title", models.CharField(max_length=80, null=True, verbose_name=b"Titre", blank=True)),
                ("slug", models.SlugField(max_length=80)),
                ("physical", easy_thumbnails.fields.ThumbnailerImageField(upload_to=zds.gallery.models.image_path)),
                ("legend", models.CharField(max_length=80, null=True, verbose_name=b"L\xc3\xa9gende", blank=True)),
                (
                    "pubdate",
                    models.DateTimeField(auto_now_add=True, verbose_name=b"Date de cr\xc3\xa9ation", db_index=True),
                ),
                ("update", models.DateTimeField(null=True, verbose_name=b"Date de modification", blank=True)),
                ("gallery", models.ForeignKey(verbose_name=b"Galerie", to="gallery.Gallery", on_delete=models.CASCADE)),
            ],
            options={
                "verbose_name": "Image",
                "verbose_name_plural": "Images",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="UserGallery",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                (
                    "mode",
                    models.CharField(default=b"R", max_length=1, choices=[(b"R", b"Lecture"), (b"W", b"Ecriture")]),
                ),
                ("gallery", models.ForeignKey(verbose_name=b"Galerie", to="gallery.Gallery", on_delete=models.CASCADE)),
                (
                    "user",
                    models.ForeignKey(verbose_name=b"Membre", to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE),
                ),
            ],
            options={
                "verbose_name": "Galeries de l'utilisateur",
                "verbose_name_plural": "Galeries de l'utilisateur",
            },
            bases=(models.Model,),
        ),
    ]
