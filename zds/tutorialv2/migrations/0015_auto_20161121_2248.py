# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import zds.utils.models
import easy_thumbnails.fields


class Migration(migrations.Migration):

    dependencies = [
        ('tutorialv2', '0014_auto_20160331_0415'),
    ]

    operations = [
        migrations.CreateModel(
            name='EditorialHelp',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=20, verbose_name=b'Name')),
                ('slug', models.SlugField(max_length=20)),
                ('description', models.CharField(max_length=150, verbose_name=b'Description')),
                ('image', easy_thumbnails.fields.ThumbnailerImageField(upload_to=zds.utils.models.image_path_help)),
            ],
            options={
                'verbose_name': 'Aide \xe0 la r\xe9daction',
                'verbose_name_plural': 'Aides \xe0 la r\xe9daction',
            },
        ),
        migrations.AlterField(
            model_name='publishablecontent',
            name='helps',
            field=models.ManyToManyField(to='tutorialv2.EditorialHelp', db_index=True, verbose_name=b'Aides', blank=True),
        ),
    ]
