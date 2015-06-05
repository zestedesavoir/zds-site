# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stats', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='log',
            name='request',
        ),
        migrations.AddField(
            model_name='log',
            name='content_type',
            field=models.CharField(default='', max_length=80, verbose_name=b'Type de contenu'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='log',
            name='id_zds',
            field=models.IntegerField(default=1, verbose_name=b'Identifiant sur ZdS'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='log',
            name='request_time',
            field=models.IntegerField(verbose_name=b'Temps de chargement de la page'),
            preserve_default=True,
        ),
    ]
