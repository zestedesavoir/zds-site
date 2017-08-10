from django.db import models, migrations

import zds.notification.models


class Migration(migrations.Migration):
    dependencies = [
        ('notification', '0002_auto_20151219_2302'),
    ]

    operations = [
        migrations.CreateModel(
            name='TopicAnswerSubscription',
            fields=[
                ('answersubscription_ptr',
                 models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False,
                                      to='notification.AnswerSubscription')),
            ],
            options={
            },
            bases=('notification.answersubscription', zds.notification.models.SingleNotificationMixin),
        ),
    ]
