# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notification', '0009_newtopicsubscription'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='is_dead',
            field=models.BooleanField(default=False, verbose_name='Morte'),
        ),
    ]
