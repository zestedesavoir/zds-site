# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forum', '0010_auto_20161112_1823'),
    ]

    operations = [
        migrations.RenameField(
            model_name='forum',
            old_name='group',
            new_name='groups',
        ),
    ]
