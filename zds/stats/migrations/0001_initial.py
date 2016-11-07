# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Browser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(max_length=80, null=True, verbose_name='Navigateur', db_index=True)),
            ],
            options={
                'verbose_name': 'Stats navigateur',
            },
        ),
        migrations.CreateModel(
            name='City',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(max_length=80, null=True, verbose_name='Ville', db_index=True)),
            ],
            options={
                'verbose_name': 'Stats Ville',
                'verbose_name_plural': 'Stats Villes',
            },
        ),
        migrations.CreateModel(
            name='Country',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(max_length=80, null=True, verbose_name='Pays', db_index=True)),
            ],
            options={
                'verbose_name': 'Stats Pays',
                'verbose_name_plural': 'Stats Pays',
            },
        ),
        migrations.CreateModel(
            name='Device',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(max_length=80, null=True, verbose_name='Device', db_index=True)),
            ],
            options={
                'verbose_name': 'Stats Device',
            },
        ),
        migrations.CreateModel(
            name='Log',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('id_zds', models.IntegerField(verbose_name=b'Identifiant sur ZdS', db_index=True)),
                ('content_type', models.CharField(max_length=80, verbose_name=b'Type de contenu', db_index=True)),
                ('hash_code', models.CharField(max_length=32, null=True, verbose_name=b'Hash code de la ligne de log')),
                ('timestamp', models.DateTimeField(verbose_name=b'Timestamp')),
                ('remote_addr', models.CharField(max_length=39, null=True, verbose_name=b'Adresse IP', db_index=True)),
                ('body_bytes_sent', models.IntegerField(verbose_name=b'Taille de la page')),
                ('dns_referal', models.CharField(max_length=80, null=True, verbose_name=b'Source', db_index=True)),
                ('os_family', models.CharField(max_length=30, null=True, verbose_name=b"Famille de systeme d'exploitation", db_index=True)),
                ('os_version', models.CharField(max_length=15, null=True, verbose_name=b"Version du systeme d'exploitation")),
                ('browser_family', models.CharField(max_length=20, null=True, verbose_name=b'Famille du navigateur', db_index=True)),
                ('browser_version', models.CharField(max_length=15, null=True, verbose_name=b'Version du navigateur')),
                ('device_family', models.CharField(max_length=20, null=True, verbose_name=b'Famille de device', db_index=True)),
                ('request_time', models.IntegerField(verbose_name=b'Temps de chargement de la page')),
                ('country', models.CharField(max_length=40, null=True, verbose_name=b'Pays', db_index=True)),
                ('city', models.CharField(max_length=40, null=True, verbose_name=b'Ville', db_index=True)),
            ],
            options={
                'verbose_name': 'Log web',
                'verbose_name_plural': 'Logs web',
            },
        ),
        migrations.CreateModel(
            name='OS',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(max_length=80, null=True, verbose_name="Syst\xe8me d'exploitaiton", db_index=True)),
            ],
            options={
                'verbose_name': 'Stats OS',
            },
        ),
        migrations.CreateModel(
            name='Source',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(max_length=80, null=True, verbose_name='Source', db_index=True)),
            ],
            options={
                'verbose_name': 'Stats Source',
                'verbose_name_plural': 'Stats Sources',
            },
        ),
        migrations.AlterIndexTogether(
            name='log',
            index_together=set([('hash_code', 'content_type', 'timestamp')]),
        ),
    ]
