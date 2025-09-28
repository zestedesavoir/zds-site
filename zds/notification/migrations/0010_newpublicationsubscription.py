from django.db import migrations, models

import zds.notification.models


class Migration(migrations.Migration):
    dependencies = [
        ("notification", "0009_newtopicsubscription"),
    ]

    operations = [
        migrations.CreateModel(
            name="NewPublicationSubscription",
            fields=[
                (
                    "subscription_ptr",
                    models.OneToOneField(
                        parent_link=True,
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        to="notification.Subscription",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            bases=("notification.subscription", zds.notification.models.MultipleNotificationsMixin),
        ),
    ]
