# Generated by Django 2.1.5 on 2019-01-14 13:01

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("mp", "0005_auto_20190110_1310"),
    ]

    operations = [
        migrations.AlterField(
            model_name="privatepost",
            name="author",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="privateposts",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Auteur",
            ),
        ),
    ]
