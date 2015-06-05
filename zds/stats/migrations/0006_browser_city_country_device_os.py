# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stats', '0005_source'),
    ]

    operations = [
        migrations.CreateModel(
            name='Browser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('browser_name', models.CharField(max_length=80, null=True, verbose_name='Navigateur')),
            ],
            options={
                'verbose_name': 'Stats navigateur',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='City',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('city', models.CharField(max_length=80, null=True, verbose_name='Ville')),
            ],
            options={
                'verbose_name': 'Stats Ville',
                'verbose_name_plural': 'Stats Villes',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Country',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('country', models.CharField(max_length=80, null=True, verbose_name='Pays')),
            ],
            options={
                'verbose_name': 'Stats Pays',
                'verbose_name_plural': 'Stats Pays',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Device',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('device_name', models.CharField(max_length=80, null=True, verbose_name='Device')),
            ],
            options={
                'verbose_name': 'Stats Device',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OS',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('os_name', models.CharField(max_length=80, null=True, verbose_name="Syst\xe8me d'exploitaiton")),
            ],
            options={
                'verbose_name': 'Stats OS',
            },
            bases=(models.Model,),
        ),
    ]
