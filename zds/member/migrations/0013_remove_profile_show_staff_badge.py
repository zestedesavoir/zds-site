# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-06-26 12:17
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('member', '0012_profile_hats'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='show_staff_badge',
        ),
    ]
