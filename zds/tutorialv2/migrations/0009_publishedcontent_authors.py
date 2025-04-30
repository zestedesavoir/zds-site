from django.conf import settings
from django.db import migrations, models


def put_authors(apps, schema_editor):
    PublishedContent = apps.get_model("tutorialv2", "PublishedContent")
    for content in PublishedContent.objects.filter(must_redirect=False).all():
        for author in content.content.authors.all():
            content.authors.add(author)
        content.save()


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("tutorialv2", "0008_publishedcontent_update_date"),
    ]

    operations = [
        migrations.AddField(
            model_name="publishedcontent",
            name="authors",
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, verbose_name=b"Auteurs", db_index=True),
            preserve_default=True,
        ),
        migrations.RunPython(put_authors),
    ]
