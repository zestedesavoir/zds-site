# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='FeaturedMessage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('hook', models.CharField(max_length=100, null=True, verbose_name='Accroche', blank=True)),
                ('message', models.CharField(max_length=255, null=True, verbose_name='Message', blank=True)),
                ('url', models.CharField(max_length=2000, null=True, verbose_name='URL du message', blank=True)),
            ],
            options={
                'verbose_name': 'Message',
                'verbose_name_plural': 'Messages',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FeaturedResource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=80, verbose_name='Titre')),
                ('type', models.CharField(max_length=80, verbose_name='Type')),
                ('authors', models.CharField(max_length=100, verbose_name='Auteurs', blank=True)),
                ('image_url', models.CharField(max_length=2000, verbose_name="URL de l'image \xe0 la une")),
                ('url', models.CharField(max_length=2000, verbose_name='URL de la une')),
                ('pubdate', models.DateTimeField(db_index=True, verbose_name='Date de publication', blank=True)),
            ],
            options={
                'verbose_name': 'Une',
                'verbose_name_plural': 'Unes',
            },
            bases=(models.Model,),
        ),
    ]
