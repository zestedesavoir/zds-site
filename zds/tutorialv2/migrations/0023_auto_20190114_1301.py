# Generated by Django 2.1.5 on 2019-01-14 13:01

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("tutorialv2", "0022_python_3"),
    ]

    operations = [
        migrations.AlterField(
            model_name="contentread",
            name="note",
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.SET_NULL, to="tutorialv2.ContentReaction"
            ),
        ),
        migrations.AlterField(
            model_name="publishablecontent",
            name="beta_topic",
            field=models.ForeignKey(
                blank=True,
                default=None,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="forum.Topic",
                verbose_name="Sujet beta associé",
            ),
        ),
        migrations.AlterField(
            model_name="publishablecontent",
            name="gallery",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="gallery.Gallery",
                verbose_name="Galerie d'images",
            ),
        ),
        migrations.AlterField(
            model_name="publishablecontent",
            name="last_note",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="last_note",
                to="tutorialv2.ContentReaction",
                verbose_name="Derniere note",
            ),
        ),
        migrations.AlterField(
            model_name="publishablecontent",
            name="licence",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="utils.Licence",
                verbose_name="Licence",
            ),
        ),
        migrations.AlterField(
            model_name="publishedcontent",
            name="must_redirect",
            field=models.BooleanField(
                blank=True, db_index=True, default=False, verbose_name="Redirection vers  une version plus récente"
            ),
        ),
        migrations.AlterField(
            model_name="validation",
            name="validator",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="author_content_validations",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Validateur",
            ),
        ),
    ]
