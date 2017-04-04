# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tutorialv2', '0020_auto_20170401_1521'),
    ]

    operations = [
        migrations.CreateModel(
            name='PickListOperation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('operation', models.CharField(db_index=True, max_length=7, choices=[('REJECT', 'Rejet\xe9'), ('NO_PICK', 'Non choisi'), ('PICK', 'Choisi')])),
                ('content', models.ForeignKey(verbose_name='Contenu propos\xe9', blank=True, to='tutorialv2.PublishableContent')),
            ],
            options={
                'verbose_name': 'Pick Operation',
                'verbose_name_plural': 'Pick Operations',
            },
        ),
    ]
