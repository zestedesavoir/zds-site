from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("member", "0005_profile_github_token"),
    ]

    operations = [
        migrations.RenameField(
            model_name="profile",
            old_name="hover_or_click",
            new_name="is_hover_enabled",
        ),
        migrations.AlterField(
            model_name="profile",
            name="is_hover_enabled",
            field=models.BooleanField(default=True, verbose_name=b"D\xc3\xa9roulement au survol ?"),
        ),
        migrations.AlterField(
            model_name="profile",
            name="end_ban_write",
            field=models.DateTimeField(null=True, verbose_name=b"Fin d'interdiction d'\xc3\xa9crire", blank=True),
        ),
    ]
