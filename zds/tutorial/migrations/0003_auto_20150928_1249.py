# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tutorial', '0002_auto_20150414_2325'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chapter',
            name='image',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name=b'Image du chapitre', blank=True, to='gallery.Image', null=True),
            preserve_default=True,
        ),
    ]
