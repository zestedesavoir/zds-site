# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tutorialv2', '0015_auto_20161121_2248'),
        ('utils', '0009_auto_20161113_2328'),
    ]

    operations = [
        migrations.DeleteModel(
            name='HelpWriting',
        ),
    ]
