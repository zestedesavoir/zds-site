from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("utils", "0006_auto_20160509_1633"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tag",
            name="slug",
            field=models.SlugField(max_length=30, verbose_name=b"Slug"),
        ),
        migrations.AlterField(
            model_name="tag",
            name="title",
            field=models.CharField(unique=True, max_length=30, verbose_name=b"Titre", db_index=True),
        ),
    ]
