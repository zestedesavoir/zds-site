# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tutorialv2', '0014_auto_20160331_0415'),
    ]

    operations = [
        migrations.AddField(
            model_name='publishablecontent',
            name='converted_to',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name='Contenu promu', blank=True, to='tutorialv2.PublishableContent', null=True),
        ),
        migrations.AddField(
            model_name='publishablecontent',
            name='sha_picked',
            field=models.CharField(db_index=True, max_length=80, null=True, verbose_name=b'Sha1 de la version approuv\xc3\xa9e (contenus avec publication sans validation)', blank=True),
        ),
        migrations.AlterField(
            model_name='publishablecontent',
            name='type',
            field=models.CharField(db_index=True, max_length=10, choices=[(b'TUTORIAL', 'Tutoriel'), (b'ARTICLE', 'Article'), (b'OPINION', 'Billet')]),
        ),
        migrations.AlterField(
            model_name='publishedcontent',
            name='content_type',
            field=models.CharField(db_index=True, max_length=10, verbose_name=b'Type de contenu', choices=[(b'TUTORIAL', 'Tutoriel'), (b'ARTICLE', 'Article'), (b'OPINION', 'Billet')]),
        ),
    ]
