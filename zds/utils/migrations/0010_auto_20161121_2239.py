# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tutorialv2', '0016_auto_20161120_1640'),
        ('utils', '0009_auto_20161113_2328'),
    ]

    operations = [
        migrations.AddField(
            model_name='alert',
            name='content',
            field=models.ForeignKey(related_name='alerts_on_this_content', verbose_name=b'Contenu', blank=True, to='tutorialv2.PublishableContent', null=True),
        ),
        migrations.AlterField(
            model_name='alert',
            name='comment',
            field=models.ForeignKey(related_name='alerts_on_this_comment', verbose_name=b'Commentaire', blank=True, to='utils.Comment', null=True),
        ),
        migrations.AlterField(
            model_name='alert',
            name='scope',
            field=models.CharField(db_index=True, max_length=10, choices=[(b'FORUM', 'Forum'), (b'CONTENT', 'Contenu'), (b'TUTORIAL', 'Tutoriel'), (b'ARTICLE', 'Article'), (b'OPINION', 'Billet')]),
        ),
    ]
