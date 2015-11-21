# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Poll',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=80, verbose_name=b'Titre')),
                ('slug', models.SlugField(max_length=80)),
                ('pubdate', models.DateTimeField(auto_now_add=True, verbose_name=b'Date de cr\xc3\xa9ation', db_index=True)),
                ('open', models.BooleanField(default=False)),
                ('user', models.ForeignKey(verbose_name='Membre', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['pubdate'],
                'verbose_name': 'Poll',
                'verbose_name_plural': 'Polls',
            },
            bases=(models.Model,),
        ),
    ]
