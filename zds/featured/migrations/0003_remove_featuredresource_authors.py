# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('featured', '0002_auto_20150622_0956'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='featuredresource',
            name='authors',
        ),
    ]
