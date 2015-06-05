# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stats', '0004_auto_20150528_1151'),
    ]

    operations = [
        migrations.CreateModel(
            name='Source',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dns_referal', models.CharField(max_length=80, null=True, verbose_name=b'Source')),
            ],
            options={
                'verbose_name': 'Stats Source',
                'verbose_name_plural': 'Stats Sources',
            },
            bases=(models.Model,),
        ),
    ]
