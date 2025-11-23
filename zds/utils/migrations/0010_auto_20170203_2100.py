import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("utils", "0009_auto_20161113_2328"),
    ]

    operations = [
        migrations.AlterField(
            model_name="alert",
            name="privatetopic",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.SET_NULL,
                verbose_name="Message priv\xe9",
                blank=True,
                to="mp.PrivateTopic",
                null=True,
            ),
        ),
    ]
