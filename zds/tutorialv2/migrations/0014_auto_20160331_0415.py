from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tutorialv2", "0013_auto_20160320_0908"),
    ]

    operations = [
        migrations.AlterField(
            model_name="publishablecontent",
            name="beta_topic",
            field=models.ForeignKey(
                default=None,
                blank=True,
                to="forum.Topic",
                null=True,
                verbose_name=b"Sujet beta associ\xc3\xa9",
                on_delete=models.CASCADE,
            ),
        ),
        migrations.AlterField(
            model_name="publishablecontent",
            name="helps",
            field=models.ManyToManyField(to="utils.HelpWriting", db_index=True, verbose_name=b"Aides", blank=True),
        ),
        migrations.AlterField(
            model_name="publishablecontent",
            name="source",
            field=models.CharField(max_length=200, null=True, verbose_name=b"Source", blank=True),
        ),
    ]
