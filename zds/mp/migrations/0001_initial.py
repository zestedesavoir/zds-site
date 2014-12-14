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
            name='PrivatePost',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('text', models.TextField(verbose_name=b'Texte')),
                ('text_html', models.TextField(verbose_name=b'Texte en HTML')),
                ('pubdate', models.DateTimeField(auto_now_add=True, verbose_name=b'Date de publication', db_index=True)),
                ('update', models.DateTimeField(null=True, verbose_name=b"Date d'\xc3\xa9dition", blank=True)),
                ('position_in_topic', models.IntegerField(verbose_name=b'Position dans le sujet', db_index=True)),
                ('author', models.ForeignKey(related_name='privateposts', verbose_name=b'Auteur', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PrivateTopic',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=80, verbose_name=b'Titre')),
                ('subtitle', models.CharField(max_length=200, verbose_name=b'Sous-titre')),
                ('pubdate', models.DateTimeField(auto_now_add=True, verbose_name=b'Date de cr\xc3\xa9ation', db_index=True)),
                ('author', models.ForeignKey(related_name='author', verbose_name=b'Auteur', to=settings.AUTH_USER_MODEL)),
                ('last_message', models.ForeignKey(related_name='last_message', verbose_name=b'Dernier message', to='mp.PrivatePost', null=True)),
                ('participants', models.ManyToManyField(related_name='participants', verbose_name=b'Participants', to=settings.AUTH_USER_MODEL, db_index=True)),
            ],
            options={
                'verbose_name': 'Message priv\xe9',
                'verbose_name_plural': 'Messages priv\xe9s',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PrivateTopicRead',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('privatepost', models.ForeignKey(to='mp.PrivatePost')),
                ('privatetopic', models.ForeignKey(to='mp.PrivateTopic')),
                ('user', models.ForeignKey(related_name='privatetopics_read', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Message priv\xe9 lu',
                'verbose_name_plural': 'Messages priv\xe9s lus',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='privatepost',
            name='privatetopic',
            field=models.ForeignKey(verbose_name=b'Message priv\xc3\xa9', to='mp.PrivateTopic'),
            preserve_default=True,
        ),
    ]
