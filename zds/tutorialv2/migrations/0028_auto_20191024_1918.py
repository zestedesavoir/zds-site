# Generated by Django 2.1.11 on 2019-10-24 19:18

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("tutorialv2", "0023_publishablecontent_validation_private_message"),
    ]

    operations = [
        migrations.CreateModel(
            name="ContentContribution",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("comment", models.CharField(blank=True, max_length=200, null=True, verbose_name="Commentaire")),
                (
                    "content",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="tutorialv2.PublishableContent",
                        verbose_name="Contenu",
                    ),
                ),
            ],
            options={
                "verbose_name": "Contribution aux contenus",
                "verbose_name_plural": "Contributions aux contenus",
            },
        ),
        migrations.CreateModel(
            name="ContentContributionRole",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=20)),
                ("subtitle", models.CharField(blank=True, max_length=200, null=True)),
                ("position", models.IntegerField(default=0)),
            ],
            options={
                "verbose_name": "Role de la contribution au contenu",
                "verbose_name_plural": "Roles de la contribution au contenu",
            },
        ),
        migrations.AddField(
            model_name="contentcontribution",
            name="contribution_role",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="tutorialv2.ContentContributionRole",
                verbose_name="role de la contribution",
            ),
        ),
        migrations.AddField(
            model_name="contentcontribution",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name="Contributeur"
            ),
        ),
    ]
