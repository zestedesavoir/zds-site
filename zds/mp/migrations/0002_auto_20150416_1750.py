from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("mp", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="privatetopic",
            name="subtitle",
            field=models.CharField(max_length=200, verbose_name="Sous-titre", blank=True),
            preserve_default=True,
        ),
    ]
