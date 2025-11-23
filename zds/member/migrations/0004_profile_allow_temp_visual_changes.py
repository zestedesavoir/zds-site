from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("member", "0003_auto_20151019_2333"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="allow_temp_visual_changes",
            field=models.BooleanField(default=True, verbose_name=b"Activer les changements visuels temporaires"),
            preserve_default=True,
        ),
    ]
