from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("tutorialv2", "0020_auto_20170401_1521"),
    ]

    operations = [
        migrations.CreateModel(
            name="PickListOperation",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                (
                    "operation",
                    models.CharField(
                        db_index=True,
                        max_length=10,
                        choices=[
                            ("REJECT", "Rejet\xe9"),
                            ("NO_PICK", "Non choisi"),
                            ("PICK", "Choisi"),
                            ("REMOVE_PUB", "D\xe9publier d\xe9finitivement"),
                        ],
                    ),
                ),
                ("operation_date", models.DateTimeField(verbose_name="Date de l'op\xe9ration", db_index=True)),
                ("version", models.CharField(max_length=128, verbose_name="Version du billet concern\xe9e")),
                ("is_effective", models.BooleanField(default=True, verbose_name="Choix actif")),
                (
                    "canceler_user",
                    models.ForeignKey(
                        related_name="canceled_pick_operations",
                        verbose_name="Mod\xe9rateur qui a annul\xe9 la d\xe9cision",
                        blank=True,
                        to=settings.AUTH_USER_MODEL,
                        null=True,
                        on_delete=models.CASCADE,
                    ),
                ),
                (
                    "content",
                    models.ForeignKey(
                        verbose_name="Contenu propos\xe9", to="tutorialv2.PublishableContent", on_delete=models.CASCADE
                    ),
                ),
                (
                    "staff_user",
                    models.ForeignKey(
                        related_name="pick_operations",
                        verbose_name="Mod\xe9rateur",
                        to=settings.AUTH_USER_MODEL,
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "verbose_name": "Choix d'un billet",
                "verbose_name_plural": "Choix des billets",
            },
        ),
    ]
