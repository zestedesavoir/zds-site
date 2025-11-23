from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("forum", "0019_post_is_potential_spam"),
    ]

    operations = [
        migrations.RenameField(model_name="post", old_name="is_potential_spam", new_name="is_potential_spam_old_field"),
    ]
