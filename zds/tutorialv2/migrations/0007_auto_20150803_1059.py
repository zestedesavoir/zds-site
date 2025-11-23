from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tutorialv2", "0006_publishablecontent_must_reindex"),
    ]

    operations = [
        migrations.AlterField(
            model_name="publishablecontent",
            name="must_reindex",
            field=models.BooleanField(default=True, verbose_name="Si le contenu doit-\xeatre r\xe9-index\xe9"),
            preserve_default=True,
        ),
    ]
