# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tutorialv2', '0014_auto_20160418_1837'),
    ]

    operations = [
        migrations.AddField(
            model_name='publishablecontent',
            name='sha_approved',
            field=models.CharField(db_index=True, max_length=80, null=True, verbose_name=b'Sha1 de la version approuv\xc3\xa9e (contenus avec publication sans validation)', blank=True),
        ),
    ]
