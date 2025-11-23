from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("forum", "0010_auto_20161112_1823"),
    ]

    operations = [
        migrations.AlterField(
            model_name="forum",
            name="group",
            field=models.ManyToManyField(
                to="auth.Group", verbose_name="Groupes autoris\xe9s (aucun = public)", blank=True
            ),
        ),
    ]
