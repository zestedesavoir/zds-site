from django.db import migrations, models

from zds.featured.models import FeaturedMessage


def remove_empty_message(*_):
    last_message = FeaturedMessage.objects.get_last_message()
    if last_message and (last_message.message is None or last_message.message.strip() == ""):
        last_message.delete()


def revert(*_):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("featured", "0007_featuredrequested"),
    ]

    operations = [
        migrations.RunPython(remove_empty_message, revert),
        migrations.AlterField(
            model_name="featuredmessage",
            name="message",
            field=models.CharField(max_length=255, verbose_name="Message"),
        ),
    ]
