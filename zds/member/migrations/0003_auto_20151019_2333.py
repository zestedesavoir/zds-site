from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("member", "0002_auto_20150601_1144"),
    ]

    operations = [
        migrations.AlterField(
            model_name="profile",
            name="sign",
            field=models.TextField(max_length=500, verbose_name=b"Signature", blank=True),
            preserve_default=True,
        ),
    ]
