from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("forum", "0006_auto_20160720_2259"),
    ]

    operations = [
        migrations.AlterField(
            model_name="category",
            name="position",
            field=models.IntegerField(default=0, verbose_name=b"Position"),
        ),
    ]
