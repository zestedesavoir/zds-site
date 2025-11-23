from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("forum", "0020_rename_post_is_potential_spam_to_temp_name_for_migration"),
        # We must remove the field AFTER data was copied from this field to the comments table.
        # This is extremely important: else, we could lose all existing potential spam marks.
        ("utils", "0023_move_potential_spam_to_comment_model"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="post",
            name="is_potential_spam_old_field",
        ),
    ]
