# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stats', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='log',
            name='browser_family',
            field=models.CharField(max_length=40, null=True, verbose_name=b'Famille du navigateur', db_index=True),
        ),
        migrations.AlterField(
            model_name='log',
            name='browser_version',
            field=models.CharField(max_length=15, null=True, verbose_name=b'Version du navigateur'),
        ),
        migrations.AlterField(
            model_name='log',
            name='city',
            field=models.CharField(max_length=80, null=True, verbose_name=b'Ville', db_index=True),
        ),
        migrations.AlterField(
            model_name='log',
            name='content_type',
            field=models.CharField(max_length=80, verbose_name=b'Type de contenu', db_index=True),
        ),
        migrations.AlterField(
            model_name='log',
            name='country',
            field=models.CharField(max_length=80, null=True, verbose_name=b'Pays', db_index=True),
        ),
        migrations.AlterField(
            model_name='log',
            name='device_family',
            field=models.CharField(max_length=20, null=True, verbose_name=b'Famille de device', db_index=True),
        ),
        migrations.AlterField(
            model_name='log',
            name='dns_referal',
            field=models.CharField(max_length=80, null=True, verbose_name=b'Source', db_index=True),
        ),
        migrations.AlterField(
            model_name='log',
            name='hash_code',
            field=models.CharField(max_length=80, null=True, verbose_name=b'Hash code de la ligne de log', db_index=True),
        ),
        migrations.AlterField(
            model_name='log',
            name='id_zds',
            field=models.IntegerField(verbose_name=b'Identifiant sur ZdS', db_index=True),
        ),
        migrations.AlterField(
            model_name='log',
            name='os_family',
            field=models.CharField(max_length=40, null=True, verbose_name=b"Famille de systeme d'exploitation", db_index=True),
        ),
        migrations.AlterField(
            model_name='log',
            name='os_version',
            field=models.CharField(max_length=15, null=True, verbose_name=b"Version du systeme d'exploitation"),
        ),
    ]
