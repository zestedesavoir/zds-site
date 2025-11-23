from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("forum", "0005_auto_20151119_2224"),
    ]

    operations = [
        migrations.AlterField(
            model_name="topic",
            name="subtitle",
            field=models.CharField(max_length=200, null=True, verbose_name=b"Sous-titre", blank=True),
        ),
    ]
