from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tutorialv2", "0007_auto_20150803_1059"),
    ]

    operations = [
        migrations.AddField(
            model_name="publishedcontent",
            name="update_date",
            field=models.DateTimeField(
                default=None, null=True, verbose_name=b"Date de mise \xc3\xa0 jour", db_index=True, blank=True
            ),
            preserve_default=True,
        ),
    ]
