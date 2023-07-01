from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("utils", "0005_commentvote"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tag",
            name="slug",
            field=models.SlugField(max_length=30),
        ),
        migrations.AlterField(
            model_name="tag",
            name="title",
            field=models.CharField(max_length=30, verbose_name=b"Titre"),
        ),
    ]
