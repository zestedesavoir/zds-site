# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('featured', '0005_auto_20160114_1604'),
    ]

    operations = [
        migrations.RenameField(
            model_name='featuredresource',
            old_name='type',
            new_name='publishable_content_type',
        ),
    ]
