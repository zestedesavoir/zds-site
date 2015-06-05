# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Log',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('remote_addr', models.CharField(max_length=39, null=True, verbose_name=b'Adresse IP', db_index=True)),
                ('hash_code', models.CharField(max_length=80, null=True, verbose_name=b'Utilisateur')),
                ('timestamp', models.DateTimeField(verbose_name=b'Timestamp', db_index=True)),
                ('request', models.TextField(verbose_name=b'Requete')),
                ('body_bytes_sent', models.IntegerField(verbose_name=b'Taille de la page')),
                ('dns_referal', models.CharField(max_length=80, null=True, verbose_name=b'Source')),
                ('os_family', models.CharField(max_length=40, null=True, verbose_name=b'Famille de systeme d\\exploitation')),
                ('os_version', models.CharField(max_length=5, null=True, verbose_name=b'Version du systeme d\\exploitation')),
                ('browser_family', models.CharField(max_length=40, null=True, verbose_name=b'Famille du navigateur')),
                ('browser_version', models.CharField(max_length=5, null=True, verbose_name=b'Version du navigateur')),
                ('device_family', models.CharField(max_length=20, null=True, verbose_name=b'Famille de device')),
                ('request_time', models.IntegerField(verbose_name=b'Temps de chargement')),
            ],
            options={
                'verbose_name': 'Log web',
                'verbose_name_plural': 'Logs web',
            },
            bases=(models.Model,),
        ),
    ]
