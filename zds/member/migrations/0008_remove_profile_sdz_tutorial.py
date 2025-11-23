from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("member", "0007_auto_20161119_1836"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="profile",
            name="sdz_tutorial",
        ),
    ]
