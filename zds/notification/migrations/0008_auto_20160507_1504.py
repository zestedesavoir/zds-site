from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("notification", "0007_auto_20160121_2343"),
    ]

    operations = [
        migrations.AlterField(
            model_name="notification",
            name="object_id",
            field=models.PositiveIntegerField(db_index=True),
        ),
        migrations.AlterField(
            model_name="subscription",
            name="object_id",
            field=models.PositiveIntegerField(db_index=True),
        ),
    ]
