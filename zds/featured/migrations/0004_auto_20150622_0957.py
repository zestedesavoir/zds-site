from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("featured", "0003_remove_featuredresource_authors"),
    ]

    operations = [
        migrations.RenameField(
            model_name="featuredresource",
            old_name="source",
            new_name="authors",
        ),
    ]
