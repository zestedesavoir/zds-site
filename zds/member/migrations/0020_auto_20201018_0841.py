from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("member", "0019_profile_username_skeleton"),
    ]

    operations = [
        migrations.AlterField(
            model_name="karmanote",
            name="note",
            field=models.TextField(verbose_name="Commentaire"),
        ),
    ]
