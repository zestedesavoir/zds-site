# Generated by Django 1.9.1 on 2016-01-06 22:31


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tutorialv2", "0010_publishedcontent_sizes"),
    ]

    operations = [
        migrations.AlterField(
            model_name="publishablecontent",
            name="subcategory",
            field=models.ManyToManyField(
                blank=True, db_index=True, to="utils.SubCategory", verbose_name=b"Sous-Cat\xc3\xa9gorie"
            ),
        ),
    ]
