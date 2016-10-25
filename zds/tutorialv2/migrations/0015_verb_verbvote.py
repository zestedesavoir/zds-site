# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tutorialv2', '0014_auto_20160331_0415'),
    ]

    operations = [
        migrations.CreateModel(
            name='Verb',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('label', models.CharField(max_length=100, verbose_name=b'The verb by itself', db_index=True)),
                ('sentence_label', models.CharField(max_length=100, verbose_name=b'The integration inside the research sentence', db_index=True)),
            ],
            options={
                'verbose_name': 'Verb',
                'verbose_name_plural': 'Verbs',
            },
        ),
        migrations.CreateModel(
            name='VerbVote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('caster', models.ForeignKey(verbose_name=b'caster', to=settings.AUTH_USER_MODEL)),
                ('content', models.ForeignKey(verbose_name=b'voted content', to='tutorialv2.PublishableContent')),
                ('verb', models.ForeignKey(verbose_name=b'voted verb', to='tutorialv2.Verb')),
            ],
        ),
    ]
