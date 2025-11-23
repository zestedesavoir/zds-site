from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("forum", "0008_auto_20161101_1122"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="topic",
            name="key",
        ),
    ]
