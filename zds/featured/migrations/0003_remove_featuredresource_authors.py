from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("featured", "0002_auto_20150622_0956"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="featuredresource",
            name="authors",
        ),
    ]
