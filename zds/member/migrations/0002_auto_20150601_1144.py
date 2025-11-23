from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("member", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="profile",
            name="avatar_url",
            field=models.CharField(max_length=2000, null=True, verbose_name=b"URL de l'avatar", blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="profile",
            name="site",
            field=models.CharField(max_length=2000, verbose_name=b"Site internet", blank=True),
            preserve_default=True,
        ),
    ]
