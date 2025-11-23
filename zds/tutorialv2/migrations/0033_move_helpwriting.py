import easy_thumbnails.fields
from django.db import migrations, models

import zds


class Migration(migrations.Migration):
    dependencies = [
        ("tutorialv2", "0032_event"),
        ("utils", "0025_move_helpwriting"),
    ]

    state_operations = [
        migrations.CreateModel(
            name="HelpWriting",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=20, verbose_name="Name")),
                ("slug", models.SlugField(max_length=20)),
                ("tablelabel", models.CharField(max_length=150, verbose_name="TableLabel")),
                ("image", easy_thumbnails.fields.ThumbnailerImageField(upload_to=zds.utils.models.image_path_help)),
            ],
            options={
                "verbose_name": "Aide à la rédaction",
                "verbose_name_plural": "Aides à la rédaction",
            },
        ),
        migrations.AlterField(
            model_name="publishablecontent",
            name="helps",
            field=models.ManyToManyField(blank=True, db_index=True, to="tutorialv2.HelpWriting", verbose_name="Aides"),
        ),
    ]

    operations = [migrations.SeparateDatabaseAndState(state_operations=state_operations)]
