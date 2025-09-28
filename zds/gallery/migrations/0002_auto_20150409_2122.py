from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("gallery", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="gallery",
            name="pubdate",
            field=models.DateTimeField(auto_now_add=True, verbose_name="Date de cr\xe9ation", db_index=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="gallery",
            name="subtitle",
            field=models.CharField(max_length=200, verbose_name="Sous titre", blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="image",
            name="legend",
            field=models.CharField(max_length=80, null=True, verbose_name="L\xe9gende", blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="image",
            name="pubdate",
            field=models.DateTimeField(auto_now_add=True, verbose_name="Date de cr\xe9ation", db_index=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="image",
            name="title",
            field=models.CharField(default="", max_length=80, verbose_name="Titre"),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="usergallery",
            name="mode",
            field=models.CharField(default=b"R", max_length=1, choices=[(b"R", "Lecture"), (b"W", "\xc9criture")]),
            preserve_default=True,
        ),
    ]
