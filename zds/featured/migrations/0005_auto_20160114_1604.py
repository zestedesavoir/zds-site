from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('featured', '0004_auto_20150622_0957'),
    ]

    operations = [
        migrations.AlterField(
            model_name='featuredresource',
            name='pubdate',
            field=models.DateTimeField(verbose_name='Date de publication', db_index=True),
            preserve_default=True,
        ),
    ]
