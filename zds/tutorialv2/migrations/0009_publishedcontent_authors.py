# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tutorialv2', '0008_publishedcontent_update_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='publishedcontent',
            name='authors',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, verbose_name=b'Auteurs', db_index=True),
            preserve_default=True,
        ),
    ]
