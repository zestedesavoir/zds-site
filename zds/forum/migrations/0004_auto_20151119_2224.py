# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('forum', '0002_auto_20150410_1505'),
    ]

    database_operations = [
        migrations.AlterModelTable('TopicFollowed', 'notification_topicfollowed')
    ]

    state_operations = [
        migrations.DeleteModel('TopicFollowed')
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=database_operations,
            state_operations=state_operations)
    ]
