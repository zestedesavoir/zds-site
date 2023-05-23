# Generated by Django 2.1.11 on 2019-12-03 10:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("tutorialv2", "0029_auto_20191123_1955"),
    ]

    operations = [
        migrations.CreateModel(
            name="ContentSuggestion",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "publication",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="publication",
                        to="tutorialv2.PublishableContent",
                        verbose_name="Contenu",
                    ),
                ),
                (
                    "suggestion",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="suggestion",
                        to="tutorialv2.PublishableContent",
                        verbose_name="Suggestion",
                    ),
                ),
            ],
        ),
    ]
