from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("member", "0004_profile_allow_temp_visual_changes"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="github_token",
            field=models.TextField(verbose_name=b"GitHub", blank=True),
        ),
    ]
