# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stats', '0006_browser_city_country_device_os'),
    ]

    operations = [
        migrations.RenameField(
            model_name='browser',
            old_name='browser_name',
            new_name='code',
        ),
        migrations.RenameField(
            model_name='city',
            old_name='city',
            new_name='code',
        ),
        migrations.RenameField(
            model_name='country',
            old_name='country',
            new_name='code',
        ),
        migrations.RenameField(
            model_name='device',
            old_name='device_name',
            new_name='code',
        ),
        migrations.RenameField(
            model_name='os',
            old_name='os_name',
            new_name='code',
        ),
        migrations.RenameField(
            model_name='source',
            old_name='dns_referal',
            new_name='code',
        ),
    ]
