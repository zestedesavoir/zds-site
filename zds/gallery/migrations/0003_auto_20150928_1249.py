from django.db import models, migrations
import zds.gallery.models
import easy_thumbnails.fields


class Migration(migrations.Migration):

    dependencies = [
        ("gallery", "0002_auto_20150409_2122"),
    ]

    operations = [
        migrations.AlterField(
            model_name="image",
            name="physical",
            field=easy_thumbnails.fields.ThumbnailerImageField(max_length=200, upload_to=zds.gallery.models.image_path),
            preserve_default=True,
        ),
    ]
