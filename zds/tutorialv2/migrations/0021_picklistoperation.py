# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tutorialv2', '0020_auto_20170401_1521'),
    ]

    operations = [
        migrations.CreateModel(
            name='PickListOperation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('operation', models.CharField(db_index=True, max_length=7, choices=[('REJECT', 'Rejet\xe9'), ('NO_PICK', 'Non choisi'), ('PICK', 'Choisi')])),
                ('operation_date', models.DateTimeField(db_index=True)),
                ('version', models.CharField(max_length=128)),
                ('is_effective', models.BooleanField(default=True, verbose_name='Choix actif')),
                ('content', models.ForeignKey(verbose_name='Contenu propos\xe9', blank=True, to='tutorialv2.PublishableContent')),
                ('staff_user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Choix des Tribunes',
                'verbose_name_plural': 'Choix des Tribunes',
            },
        ),
    ]
