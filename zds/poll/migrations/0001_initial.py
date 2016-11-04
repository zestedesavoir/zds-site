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
            name='Choice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('choice', models.CharField(max_length=200, verbose_name=b'Choix')),
            ],
            options={
                'verbose_name': 'Choix',
                'verbose_name_plural': 'Choix',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MultipleVote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('choice', models.ForeignKey(to='poll.Choice')),
            ],
            options={
                'verbose_name': 'Votes multiple',
                'verbose_name_plural': 'Multiple Votes',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Poll',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=80, verbose_name=b'Titre')),
                ('slug', models.SlugField(max_length=80)),
                ('pubdate', models.DateTimeField(auto_now_add=True, verbose_name='Date de cr\xe9ation', db_index=True)),
                ('enddate', models.DateTimeField(null=True, verbose_name='Date de fin', blank=True)),
                ('activate', models.BooleanField(default=True)),
                ('anonymous_vote', models.BooleanField(default=True, verbose_name='Vote anonyme')),
                ('type_vote', models.CharField(default=b'u', max_length=1, verbose_name=b'Type de vote', choices=[(b'u', b'Vote unique'), (b'm', b'Vote multiple')])),
                ('author', models.ForeignKey(related_name='polls', verbose_name=b'Auteur', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-pubdate'],
                'verbose_name': 'Sondage',
                'verbose_name_plural': 'Sondages',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UniqueVote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('choice', models.ForeignKey(to='poll.Choice')),
                ('poll', models.ForeignKey(to='poll.Poll')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Vote unique',
                'verbose_name_plural': 'Votes uniques',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='uniquevote',
            unique_together=set([('user', 'choice'), ('user', 'poll')]),
        ),
        migrations.AddField(
            model_name='multiplevote',
            name='poll',
            field=models.ForeignKey(to='poll.Poll'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='multiplevote',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='multiplevote',
            unique_together=set([('user', 'choice', 'poll')]),
        ),
        migrations.AddField(
            model_name='choice',
            name='poll',
            field=models.ForeignKey(related_name='choices', to='poll.Poll'),
            preserve_default=True,
        ),
    ]
