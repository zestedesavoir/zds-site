# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('poll', '0004_auto_20151121_1743'),
    ]

    operations = [
        migrations.CreateModel(
            name='MultipleVote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('choice', models.ForeignKey(to='poll.Choice')),
                ('poll', models.ForeignKey(to='poll.Poll')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
                'verbose_name': 'Vote',
                'verbose_name_plural': 'Votes',
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
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='uniquevote',
            unique_together=set([('user', 'choice'), ('user', 'poll')]),
        ),
        migrations.AlterUniqueTogether(
            name='multiplevote',
            unique_together=set([('user', 'choice')]),
        ),
        migrations.AlterModelOptions(
            name='choice',
            options={'verbose_name': 'Choice', 'verbose_name_plural': 'Choices'},
        ),
        migrations.AlterModelOptions(
            name='poll',
            options={'ordering': ['-pubdate'], 'verbose_name': 'Poll', 'verbose_name_plural': 'Polls'},
        ),
        migrations.AddField(
            model_name='poll',
            name='unique_vote',
            field=models.BooleanField(default=True, verbose_name=b'Choix unique'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='poll',
            name='anonymous_vote',
            field=models.BooleanField(default=True, verbose_name=b'Vote anonyme'),
            preserve_default=True,
        ),
    ]
