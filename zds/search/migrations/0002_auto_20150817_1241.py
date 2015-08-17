# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='searchindexcontainer',
            name='title',
            field=models.CharField(max_length=200, verbose_name=b'Titre'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='searchindexcontent',
            name='licence',
            field=models.CharField(max_length=200, verbose_name=b'Licence du contenu'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='searchindexextract',
            name='title',
            field=models.CharField(max_length=200, verbose_name=b'Titre'),
            preserve_default=True,
        ),
    ]
