from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("forum", "0007_auto_20160827_2035"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="forum",
            name="image",
        ),
    ]
