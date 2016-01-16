# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('utils', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='editor',
            field=models.ForeignKey(related_name='comments-editor+', verbose_name=b'Editeur', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
