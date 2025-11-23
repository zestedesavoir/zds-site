from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("forum", "0002_auto_20150410_1505"),
    ]

    operations = [
        migrations.AlterField(
            model_name="forum",
            name="group",
            field=models.ManyToManyField(
                to="auth.Group", verbose_name=b"Groupe autoris\xc3\xa9s (Aucun = public)", blank=True
            ),
        ),
        migrations.AlterField(
            model_name="topic",
            name="tags",
            field=models.ManyToManyField(to="utils.Tag", db_index=True, verbose_name=b"Tags du forum", blank=True),
        ),
    ]
