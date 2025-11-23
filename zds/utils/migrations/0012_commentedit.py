from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("utils", "0011_auto_20170401_1521"),
    ]

    operations = [
        migrations.CreateModel(
            name="CommentEdit",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                (
                    "date",
                    models.DateTimeField(
                        db_column="edit_date", auto_now_add=True, verbose_name="Date de l'\xe9dition", db_index=True
                    ),
                ),
                ("original_text", models.TextField(verbose_name="Contenu d'origine", blank=True)),
                (
                    "deleted_at",
                    models.DateTimeField(db_index=True, null=True, verbose_name="Date de suppression", blank=True),
                ),
                (
                    "comment",
                    models.ForeignKey(
                        related_name="edits", verbose_name="Message", to="utils.Comment", on_delete=models.CASCADE
                    ),
                ),
                (
                    "deleted_by",
                    models.ForeignKey(
                        related_name="deleted_edits",
                        verbose_name="Supprim\xe9 par",
                        blank=True,
                        to=settings.AUTH_USER_MODEL,
                        null=True,
                        on_delete=models.CASCADE,
                    ),
                ),
                (
                    "editor",
                    models.ForeignKey(
                        related_name="edits",
                        verbose_name="\xc9diteur",
                        to=settings.AUTH_USER_MODEL,
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "verbose_name": "\xc9dition d'un message",
                "verbose_name_plural": "\xc9ditions de messages",
            },
        ),
    ]
