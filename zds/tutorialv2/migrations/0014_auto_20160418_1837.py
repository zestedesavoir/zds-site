# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tutorialv2', '0013_auto_20160320_0908'),
    ]

    operations = [
        migrations.AlterField(
            model_name='publishablecontent',
            name='type',
            field=models.CharField(db_index=True, max_length=10, choices=[(b'TUTORIAL', b'Tutoriel'), (b'ARTICLE', b'Article'), (b'OPINION', b'Billet')]),
        ),
        migrations.AlterField(
            model_name='publishedcontent',
            name='content_type',
            field=models.CharField(db_index=True, max_length=10, verbose_name=b'Type de contenu', choices=[(b'TUTORIAL', b'Tutoriel'), (b'ARTICLE', b'Article'), (b'OPINION', b'Billet')]),
        ),
    ]
