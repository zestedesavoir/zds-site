from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("member", "0002_auto_20150601_1144"),
    ]

    operations = [
        migrations.CreateModel(
            name="FeaturedMessage",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                ("message", models.CharField(max_length=255, verbose_name="Message")),
                ("url", models.CharField(max_length=2000, verbose_name="URL du message")),
            ],
            options={
                "verbose_name": "Message",
                "verbose_name_plural": "Messages",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="FeaturedResource",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                ("title", models.CharField(max_length=80, verbose_name="Titre")),
                ("type", models.CharField(max_length=80, verbose_name="Type")),
                ("image_url", models.CharField(max_length=2000, verbose_name="URL de l'image \xe0 la une")),
                ("url", models.CharField(max_length=2000, verbose_name="URL de la une")),
                ("pubdate", models.DateTimeField(db_index=True, verbose_name="Date de publication", blank=True)),
                ("authors", models.ManyToManyField(to="member.Profile", verbose_name="Auteurs", db_index=True)),
            ],
            options={
                "verbose_name": "Une",
                "verbose_name_plural": "Unes",
            },
            bases=(models.Model,),
        ),
    ]
