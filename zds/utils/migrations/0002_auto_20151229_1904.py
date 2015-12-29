# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('utils', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='slug',
            field=models.SlugField(unique=True, max_length=80),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='category',
            name='title',
            field=models.CharField(unique=True, max_length=80, verbose_name=b'Titre'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='subcategory',
            name='slug',
            field=models.SlugField(unique=True, max_length=80),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='subcategory',
            name='title',
            field=models.CharField(unique=True, max_length=80, verbose_name=b'Titre'),
            preserve_default=True,
        ),
    ]
