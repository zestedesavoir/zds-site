from django.db import models, migrations
import zds.notification.models


class Migration(migrations.Migration):

    dependencies = [
        ('notification', '0004_auto_20160110_1221'),
    ]

    operations = [
        migrations.CreateModel(
            name='PrivateTopicAnswerSubscription',
            fields=[
                ('answersubscription_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='notification.AnswerSubscription')),
            ],
            options={
            },
            bases=('notification.answersubscription', zds.notification.models.SingleNotificationMixin),
        ),
    ]
