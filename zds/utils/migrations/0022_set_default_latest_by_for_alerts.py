# Generated by Django 2.2.14 on 2020-08-28 18:02

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("utils", "0021_auto_20180826_1616"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="alert",
            options={"get_latest_by": "pubdate", "verbose_name": "Alerte", "verbose_name_plural": "Alertes"},
        ),
    ]
