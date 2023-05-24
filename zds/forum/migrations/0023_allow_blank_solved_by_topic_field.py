# Generated by Django 3.2.14 on 2022-08-13 23:08

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("forum", "0022_topic_github_repository_name"),
    ]

    operations = [
        migrations.AlterField(
            model_name="topic",
            name="solved_by",
            field=models.ForeignKey(
                blank=True,
                default=None,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to=settings.AUTH_USER_MODEL,
                verbose_name="Utilisateur ayant noté le sujet comme résolu",
            ),
        ),
    ]
