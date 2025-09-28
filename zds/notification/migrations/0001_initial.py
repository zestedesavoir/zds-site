from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("forum", "0005_auto_20151119_2224"),
    ]

    state_operations = [
        migrations.CreateModel(
            name="TopicFollowed",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                ("email", models.BooleanField(default=False, db_index=True, verbose_name=b"Notification par courriel")),
                ("topic", models.ForeignKey(to="forum.Topic", on_delete=models.CASCADE)),
                (
                    "user",
                    models.ForeignKey(
                        related_name="topics_followed", to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE
                    ),
                ),
            ],
            options={
                "verbose_name": "Sujet suivi",
                "verbose_name_plural": "Sujets suivis",
                "db_table": "notification_topicfollowed",
            },
            bases=(models.Model,),
        ),
    ]

    operations = [migrations.SeparateDatabaseAndState(state_operations=state_operations)]
