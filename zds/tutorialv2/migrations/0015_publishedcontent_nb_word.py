# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tutorialv2', '0014_auto_20160331_0415'),
    ]

    operations = [
        migrations.AddField(
            model_name='publishedcontent',
            name='nb_word',
            field=models.IntegerField(default=None, null=True, verbose_name=b'Nombre de mots du contenu', blank=True),
        ),
    ]
