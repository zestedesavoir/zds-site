# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tutorialv2', '0015_auto_20161120_1640'),
    ]

    operations = [
        migrations.AddField(
            model_name='publishedcontent',
            name='nb_letter',
            field=models.IntegerField(default=None, null=True, verbose_name=b'Nombre de lettres du contenu', blank=True),
        ),
        migrations.AlterField(
            model_name='publishablecontent',
            name='converted_to',
            field=models.ForeignKey(related_name='converted_from', on_delete=django.db.models.deletion.SET_NULL, verbose_name='Contenu promu', blank=True, to='tutorialv2.PublishableContent', null=True),
        ),
        migrations.AlterField(
            model_name='publishablecontent',
            name='sha_picked',
            field=models.CharField(db_index=True, max_length=80, null=True, verbose_name='Sha1 de la version choisie (contenus publi\xe9s sans validation)', blank=True),
        ),
    ]
