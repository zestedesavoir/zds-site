from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tutorialv2", "0017_auto_20170204_2239"),
    ]

    operations = [
        migrations.AddField(
            model_name="publishedcontent",
            name="is_obsolete",
            field=models.BooleanField(default=False, verbose_name="Est obsol\xe8te"),
        ),
    ]
