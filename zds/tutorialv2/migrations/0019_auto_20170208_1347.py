from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tutorialv2", "0018_publishedcontent_is_obsolete"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="publishedcontent",
            name="is_obsolete",
        ),
        migrations.AddField(
            model_name="publishablecontent",
            name="is_obsolete",
            field=models.BooleanField(default=False, verbose_name="Est obsol\xe8te"),
        ),
    ]
