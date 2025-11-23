from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("forum", "0009_remove_topic_key"),
    ]

    operations = [
        migrations.AlterField(
            model_name="topic",
            name="title",
            field=models.CharField(max_length=160, verbose_name=b"Titre"),
        ),
    ]
