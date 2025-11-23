from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("forum", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="category",
            options={
                "ordering": ["position", "title"],
                "verbose_name": "Cat\xe9gorie",
                "verbose_name_plural": "Cat\xe9gories",
            },
        ),
        migrations.AlterModelOptions(
            name="forum",
            options={
                "ordering": ["position_in_category", "title"],
                "verbose_name": "Forum",
                "verbose_name_plural": "Forums",
            },
        ),
    ]
