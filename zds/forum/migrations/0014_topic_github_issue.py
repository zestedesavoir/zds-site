from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("forum", "0013_auto_20170327_1349"),
    ]

    operations = [
        migrations.AddField(
            model_name="topic",
            name="github_issue",
            field=models.PositiveIntegerField(null=True, verbose_name="Ticket GitHub", blank=True),
        ),
    ]
