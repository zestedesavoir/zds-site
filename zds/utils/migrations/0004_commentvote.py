# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('utils', '0003_auto_20150414_2256'),
    ]

    operations = [
        migrations.CreateModel(
            name='CommentVote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('positive', models.BooleanField(default=True, verbose_name=b'Est un vote positif')),
                ('comment', models.ForeignKey(to='utils.Comment')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Vote',
                'verbose_name_plural': 'Votes',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='commentvote',
            unique_together=set([('user', 'comment')]),
        ),
        migrations.RunSQL((
            'INSERT INTO utils_commentvote (comment_id, user_id, positive) '
            'SELECT t1.comments_id as comment_id, t1.user_id as user_id, 1 as positive '
            'FROM utils_commentlike t1 '
            'UNION SELECT t2.comments_id as comment_id, t2.user_id as user_id, 0 as positive '
            'FROM utils_commentdislike t2;'
            ), reverse_sql=(
            'INSERT INTO utils_commentlike (comments_id, user_id) '
            'SELECT vote.comment_id as comments_id, vote.user_id as user_id '
            'FROM utils_commentvote vote '
            'WHERE vote.positive = 1;'

            'INSERT INTO utils_commentdislike (comments_id, user_id) '
            'SELECT vote.comment_id as comments_id, vote.user_id as user_id '
            'FROM utils_commentvote vote '
            'WHERE vote.positive = 0')
        ),
        migrations.RunSQL((
            'UPDATE utils_comment '
            'SET `like` = (SELECT COUNT(*) FROM utils_commentvote votes WHERE votes.comment_id = utils_comment.id AND votes.positive = 1), '
            '`dislike` = (SELECT COUNT(*) FROM utils_commentvote votes WHERE votes.comment_id = utils_comment.id AND votes.positive = 0);'
        ), reverse_sql=""),
        migrations.RemoveField(
            model_name='commentdislike',
            name='comments',
        ),
        migrations.RemoveField(
            model_name='commentdislike',
            name='user',
        ),
        migrations.DeleteModel(
            name='CommentDislike',
        ),
        migrations.RemoveField(
            model_name='commentlike',
            name='comments',
        ),
        migrations.RemoveField(
            model_name='commentlike',
            name='user',
        ),
        migrations.DeleteModel(
            name='CommentLike',
        ),
    ]
