from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("contenttypes", "0001_initial"),
        ("member", "0004_profile_allow_temp_visual_changes"),
        ("notification", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Notification",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                ("pubdate", models.DateTimeField(auto_now_add=True, verbose_name="Date de cr\xe9ation", db_index=True)),
                ("object_id", models.PositiveIntegerField()),
                ("is_read", models.BooleanField(default=False, db_index=True, verbose_name="Lue")),
                ("url", models.CharField(max_length=255, verbose_name=b"URL")),
                ("title", models.CharField(max_length=200, verbose_name=b"Titre")),
                ("content_type", models.ForeignKey(to="contenttypes.ContentType", on_delete=models.CASCADE)),
                ("sender", models.ForeignKey(related_name="sender", to="member.Profile", on_delete=models.CASCADE)),
            ],
            options={
                "verbose_name": "Notification",
                "verbose_name_plural": "Notifications",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Subscription",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                ("pubdate", models.DateTimeField(auto_now_add=True, verbose_name="Date de cr\xe9ation", db_index=True)),
                ("is_active", models.BooleanField(default=True, db_index=True, verbose_name="Actif")),
                ("by_email", models.BooleanField(default=False, verbose_name="Recevoir un email")),
                ("object_id", models.PositiveIntegerField()),
            ],
            options={
                "verbose_name": "Abonnement",
                "verbose_name_plural": "Abonnements",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="AnswerSubscription",
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
            options={},
            bases=("notification.subscription",),
        ),
        migrations.AddField(
            model_name="subscription",
            name="content_type",
            field=models.ForeignKey(to="contenttypes.ContentType", on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="subscription",
            name="last_notification",
            field=models.ForeignKey(
                related_name="last_notification",
                default=None,
                to="notification.Notification",
                null=True,
                on_delete=models.CASCADE,
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="subscription",
            name="profile",
            field=models.ForeignKey(related_name="subscriber", to="member.Profile", on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="notification",
            name="subscription",
            field=models.ForeignKey(
                related_name="subscription", to="notification.Subscription", on_delete=models.CASCADE
            ),
            preserve_default=True,
        ),
    ]
