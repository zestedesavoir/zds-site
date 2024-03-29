# Generated by Django 3.2.19 on 2023-06-18 11:36

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tutorialv2", "0037_labels"),
    ]

    operations = [
        migrations.AlterField(
            model_name="goal",
            name="slug",
            field=models.SlugField(
                max_length=80,
                unique=True,
                validators=[
                    django.core.validators.RegexValidator(
                        "^non-classes$", inverse_match=True, message="Ce slug est réservé."
                    )
                ],
            ),
        ),
    ]
