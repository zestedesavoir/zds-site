from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0002_auto_20150817_1241'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='searchindexcontent',
            name='pub_date',
        ),
        migrations.AddField(
            model_name='searchindexcontent',
            name='pubdate',
            field=models.DateTimeField(default=datetime.datetime(2015, 8, 20, 19, 50, 47, 882230), verbose_name=b'Date de cr\xc3\xa9ation'),
            preserve_default=False,
        ),
    ]
