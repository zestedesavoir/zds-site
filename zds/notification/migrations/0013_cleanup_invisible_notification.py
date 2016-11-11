# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

from zds.forum.models import mark_read


def cleanup(apps, *_):
    post_class = apps.get_model("forum", "Post")
    notification_class = apps.get_model("notification", "Notification")
    for post in post_class.objects.filter(is_visible=False):
        notification_class.objects.filter(notification_url=post.get_absolute_url()).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('notification', '0012_auto_20160703_2255'),
    ]

    operations = [
        migrations.RunPython(cleanup),
    ]
