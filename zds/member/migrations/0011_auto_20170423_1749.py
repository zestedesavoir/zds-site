# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('member', '0010_bannedemailprovider_newemailprovider'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bannedemailprovider',
            name='provider',
            field=models.CharField(unique=True, max_length=253, verbose_name='Fournisseur', db_index=True),
        ),
        migrations.AlterField(
            model_name='newemailprovider',
            name='provider',
            field=models.CharField(unique=True, max_length=253, verbose_name='Fournisseur', db_index=True),
        ),
    ]
