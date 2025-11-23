from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0006_require_contenttypes_0002"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="GroupContact",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                ("name", models.CharField(unique=True, max_length=32, verbose_name=b"Nom (ex: Le staff)")),
                ("description", models.TextField(null=True, verbose_name=b"Description (en markdown)", blank=True)),
                (
                    "email",
                    models.EmailField(max_length=254, null=True, verbose_name=b"Adresse mail du groupe", blank=True),
                ),
                ("position", models.PositiveSmallIntegerField(unique=True, verbose_name=b"Position dans la page")),
                (
                    "group",
                    models.OneToOneField(
                        verbose_name=b"Groupe d'utilisateur", to="auth.Group", on_delete=models.CASCADE
                    ),
                ),
                (
                    "person_in_charge",
                    models.ForeignKey(
                        verbose_name=b"Responsable",
                        blank=True,
                        to=settings.AUTH_USER_MODEL,
                        null=True,
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "verbose_name": "Groupe de la page de contact",
                "verbose_name_plural": "Groupes de la page de contact",
            },
        ),
    ]
