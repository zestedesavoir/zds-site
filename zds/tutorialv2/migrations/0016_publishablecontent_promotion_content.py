# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tutorialv2', '0015_publishablecontent_sha_approved'),
    ]

    operations = [
        migrations.AddField(
            model_name='publishablecontent',
            name='promotion_content',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name='Contenu promu', blank=True, to='tutorialv2.PublishableContent', null=True),
        ),
    ]
