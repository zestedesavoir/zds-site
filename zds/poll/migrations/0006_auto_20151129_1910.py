# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('poll', '0005_auto_20151122_0947'),
    ]

    operations = [
        migrations.CreateModel(
            name='RangeVote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('range', models.IntegerField(choices=[(2, b'Tr\xc3\xa8s favorable'), (1, b'Favorable'), (0, b'Indiff\xc3\xa9rent'), (-1, b'Hostile'), (-2, b'Tr\xc3\xa8s hostile')])),
                ('choice', models.ForeignKey(to='poll.Choice')),
                ('poll', models.ForeignKey(to='poll.Poll')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Vote par valeurs',
                'verbose_name_plural': 'Votes par valeurs',
            },
            bases=(models.Model,),
        ),
        migrations.AlterModelOptions(
            name='choice',
            options={'verbose_name': 'Choix', 'verbose_name_plural': 'Choix'},
        ),
        migrations.AlterModelOptions(
            name='multiplevote',
            options={'verbose_name': 'Votes multiple', 'verbose_name_plural': 'Multiple Votes'},
        ),
        migrations.AlterModelOptions(
            name='poll',
            options={'ordering': ['-pubdate'], 'verbose_name': 'Sondage', 'verbose_name_plural': 'sondages'},
        ),
        migrations.AlterModelOptions(
            name='uniquevote',
            options={'verbose_name': 'Vote unique', 'verbose_name_plural': 'Votes uniques'},
        ),
        migrations.AddField(
            model_name='poll',
            name='type_vote',
            field=models.CharField(default=b'uniquevote', max_length=1, choices=[(b'u', b'Vote unique'), (b'm', b'Vote multiple'), (b'r', b'Vote par valeurs')]),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='multiplevote',
            unique_together=set([]),
        ),
    ]
