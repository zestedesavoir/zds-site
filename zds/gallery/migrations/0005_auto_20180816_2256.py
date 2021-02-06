# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2018-08-16 22:56
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("gallery", "0004_python_3"),
    ]

    operations = [
        migrations.AlterField(
            model_name="usergallery",
            name="mode",
            field=models.CharField(
                choices=[("R", "Affichage"), ("W", "Affichage et modification")], default="R", max_length=1
            ),
        ),
    ]
