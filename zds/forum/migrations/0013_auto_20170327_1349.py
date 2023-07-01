from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("forum", "0012_auto_20170204_2239"),
    ]

    operations = [
        migrations.RenameField(
            model_name="forum",
            old_name="group",
            new_name="groups",
        ),
    ]
