from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("member", "0009_profile_show_staff_badge"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="show_markdown_help",
            field=models.BooleanField(
                default=True, verbose_name="Afficher l\u2019aide Markdown dans l\u2019\xe9diteur"
            ),
        ),
    ]
