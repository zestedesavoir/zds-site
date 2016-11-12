# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import zds.notification.models


class Migration(migrations.Migration):

    dependencies = [
        ('notification', '0012_auto_20160703_2255'),
    ]

    operations = [
        migrations.CreateModel(
            name='PingSubscription',
            fields=[
                ('answersubscription_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='notification.AnswerSubscription')),
            ],
            bases=('notification.answersubscription', zds.notification.models.MultipleNotificationsMixin),
        ),
    ]
