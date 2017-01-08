# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tutorialv2', '0015_publishedcontent_nb_letter'),
    ]

    operations = [
        migrations.AddField(
            model_name='publishedcontent',
            name='es_already_indexed',
            field=models.BooleanField(default=False, db_index=True, verbose_name=b'D\xc3\xa9j\xc3\xa0 index\xc3\xa9 par ES'),
        ),
        migrations.AddField(
            model_name='publishedcontent',
            name='es_flagged',
            field=models.BooleanField(default=True, db_index=True, verbose_name=b'Doit \xc3\xaatre (r\xc3\xa9)index\xc3\xa9 par ES'),
        ),
        migrations.AlterField(
            model_name='publishedcontent',
            name='nb_letter',
            field=models.IntegerField(default=None, null=True, verbose_name=b'Nombre de lettres du contenu', blank=True),
        ),
    ]
