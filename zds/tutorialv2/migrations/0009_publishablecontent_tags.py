# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('utils', '0001_initial'),
        ('tutorialv2', '0008_publishedcontent_update_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='publishablecontent',
            name='tags',
            field=models.ManyToManyField(db_index=True, to='utils.Tag', null=True, verbose_name=b'Tags du contenu', blank=True),
            preserve_default=True,
        ),
    ]
