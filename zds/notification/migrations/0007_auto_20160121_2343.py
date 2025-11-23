from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("notification", "0006_auto_20160115_1724"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="subscription",
            name="profile",
        ),
        migrations.AddField(
            model_name="subscription",
            name="user",
            field=models.ForeignKey(
                related_name="subscriber", default=None, to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="notification",
            name="sender",
            field=models.ForeignKey(related_name="sender", to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
