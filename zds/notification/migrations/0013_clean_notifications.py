# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

from zds.notification.models import TopicAnswerSubscription


def cleanup(apps, *_):
    topic_class = apps.get_model("forum", "Topic")
    for topic in topic_class.objects.filter(group__isnull=False).all():
        TopicAnswerSubscription.objects.unfollow_and_mark_read_everybody_at(topic)


class Migration(migrations.Migration):

    dependencies = [
        ('notification', '0012_auto_20160703_2255'),
    ]

    operations = [
        migrations.RunPython(cleanup),
    ]
