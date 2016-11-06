# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.db.migrations import migration
from django.db.models.aggregates import Count


def force_uniticy(schema, schema_editor):
    model_before_migration = schema.get_model('zds.forums', 'topicread')
    for t_read in model_before_migration.objects.annotate(nb_key=Count('topic', 'user')).filter(nb_key__gt=1):
        for to_be_remove in model_before_migration.objects.filter(topic__pk=t_read.topic.pk,
                                                                  user__pk=t_read.user.pk)[1:]:
            to_be_remove.remove()


class Migration(migrations.Migration):

    dependencies = [
        ('forum', '0008_remove_forum_image'),
    ]

    operations = [
        migrations.RunPython(force_uniticy),
        migrations.AlterUniqueTogether(
            name='topicread',
            unique_together=set([('topic', 'user')]),
        ),
    ]
