# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forum', '0010_auto_20161112_1823'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='es_already_indexed',
            field=models.BooleanField(default=False, db_index=True, verbose_name=b'D\xc3\xa9j\xc3\xa0 index\xc3\xa9 par ES'),
        ),
        migrations.AddField(
            model_name='post',
            name='es_flagged',
            field=models.BooleanField(default=True, db_index=True, verbose_name=b'Doit \xc3\xaatre (r\xc3\xa9)index\xc3\xa9 par ES'),
        ),
        migrations.AddField(
            model_name='topic',
            name='es_already_indexed',
            field=models.BooleanField(default=False, db_index=True, verbose_name=b'D\xc3\xa9j\xc3\xa0 index\xc3\xa9 par ES'),
        ),
        migrations.AddField(
            model_name='topic',
            name='es_flagged',
            field=models.BooleanField(default=True, db_index=True, verbose_name=b'Doit \xc3\xaatre (r\xc3\xa9)index\xc3\xa9 par ES'),
        ),
    ]
