# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('utils', '0009_auto_20161113_2328'),
    ]

    operations = [
        migrations.AlterField(
            model_name='alert',
            name='scope',
            field=models.CharField(db_index=True, max_length=10, choices=[(b'FORUM', 'Forum'), (b'TUTORIAL', 'Tutoriel'), (b'ARTICLE', 'Article'), (b'OPINION', 'Billet')]),
        ),
    ]
