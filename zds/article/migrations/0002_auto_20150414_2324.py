# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('article', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='subcategory',
            field=models.ManyToManyField(to='utils.SubCategory', db_index=True, verbose_name=b'Sous-Cat\xc3\xa9gorie', blank=True),
        ),
    ]
