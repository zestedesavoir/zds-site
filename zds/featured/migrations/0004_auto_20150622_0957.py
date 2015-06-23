# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('featured', '0003_remove_featuredresource_authors'),
    ]

    operations = [
        migrations.RenameField(
            model_name='featuredresource',
            old_name='source',
            new_name='authors',
        ),
    ]
