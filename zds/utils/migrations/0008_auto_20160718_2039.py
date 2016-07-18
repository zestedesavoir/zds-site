# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('utils', '0007_auto_20160511_2153'),
    ]

    operations = [
        migrations.AlterField(
            model_name='categorysubcategory',
            name='is_main',
            field=models.BooleanField(default=True, verbose_name=b'Est la cat\xc3\xa9gorie principale'),
        ),
    ]
