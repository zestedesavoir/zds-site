# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-06-18 17:52
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('member', '0011_bannedemailprovider_newemailprovider'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='licence',
            field=models.TextField(blank=True, null=True, verbose_name='Licence pr\xe9f\xe9r\xe9e'),
        ),
    ]
