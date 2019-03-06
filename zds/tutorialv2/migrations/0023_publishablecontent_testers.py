# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-03-03 20:44
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tutorialv2', '0022_python_3'),
    ]

    operations = [
        migrations.AddField(
            model_name='publishablecontent',
            name='testers',
            field=models.ManyToManyField(db_index=True, related_name='testers', to=settings.AUTH_USER_MODEL, verbose_name='Testeurs'),
        ),
        migrations.AlterField(
            model_name='publishablecontent',
            name='authors',
            field=models.ManyToManyField(db_index=True, related_name='authors', to=settings.AUTH_USER_MODEL, verbose_name='Auteurs'),
        ),
    ]
