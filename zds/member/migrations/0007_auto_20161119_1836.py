from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("member", "0006_auto_20161119_1650"),
    ]

    operations = [
        migrations.RenameField(
            model_name="ban",
            old_name="text",
            new_name="note",
        ),
        migrations.RenameField(
            model_name="karmanote",
            old_name="value",
            new_name="karma",
        ),
        migrations.RenameField(
            model_name="karmanote",
            old_name="staff",
            new_name="moderator",
        ),
        migrations.RenameField(
            model_name="karmanote",
            old_name="comment",
            new_name="note",
        ),
        migrations.RenameField(
            model_name="karmanote",
            old_name="create_at",
            new_name="pubdate",
        ),
    ]
