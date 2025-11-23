from django.db import migrations, models

from zds.forum.models import TopicRead


def force_unicity(*args, **kwargs):
    unique_fields = ["topic", "user"]
    duplicates = (
        TopicRead.objects.values(*unique_fields)
        .order_by()
        .annotate(max_id=models.Max("id"), count_id=models.Count("id"))
        .filter(count_id__gt=1)
    )

    for duplicate in duplicates:
        print("deleting a duplicate")
        (TopicRead.objects.filter(**{x: duplicate[x] for x in unique_fields}).exclude(id=duplicate["max_id"]).delete())


class Migration(migrations.Migration):
    dependencies = [
        ("forum", "0008_remove_forum_image"),
    ]

    operations = [
        migrations.RunPython(force_unicity),
        migrations.AlterUniqueTogether(
            name="topicread",
            unique_together={("topic", "user")},
        ),
    ]
