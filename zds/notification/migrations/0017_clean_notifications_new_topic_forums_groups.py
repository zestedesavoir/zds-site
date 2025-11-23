from django.db import migrations

from zds.forum.models import Forum, Topic
from zds.notification.models import NewTopicSubscription


def cleanup(apps, *_):
    for forum in Forum.objects.filter(groups__isnull=False).all():
        for subscription in NewTopicSubscription.objects.get_subscriptions(forum):
            if not forum.can_read(subscription.user):
                subscription.is_active = False
                if subscription.last_notification:
                    subscription.last_notification.is_read = True
                    subscription.last_notification.save()
                subscription.save()


class Migration(migrations.Migration):
    dependencies = [
        ("notification", "0016_auto_20190114_1301"),
    ]

    operations = [
        migrations.RunPython(cleanup),
    ]
