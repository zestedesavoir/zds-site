from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Ban",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                ("type", models.CharField(max_length=80, verbose_name=b"Type", db_index=True)),
                ("text", models.TextField(verbose_name=b"Explication de la sanction")),
                (
                    "pubdate",
                    models.DateTimeField(db_index=True, null=True, verbose_name=b"Date de publication", blank=True),
                ),
                (
                    "moderator",
                    models.ForeignKey(
                        related_name="bans",
                        verbose_name=b"Moderateur",
                        to=settings.AUTH_USER_MODEL,
                        on_delete=models.CASCADE,
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        verbose_name=b"Sanctionn\xc3\xa9", to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE
                    ),
                ),
            ],
            options={
                "verbose_name": "Sanction",
                "verbose_name_plural": "Sanctions",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="KarmaNote",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                ("comment", models.CharField(max_length=150, verbose_name=b"Commentaire")),
                ("value", models.IntegerField(verbose_name=b"Valeur")),
                ("create_at", models.DateTimeField(auto_now_add=True, verbose_name=b"Date d'ajout")),
                (
                    "staff",
                    models.ForeignKey(
                        related_name="karmanote_staff", to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        related_name="karmanote_user", to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE
                    ),
                ),
            ],
            options={
                "verbose_name": "Note de karma",
                "verbose_name_plural": "Notes de karma",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Profile",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                ("last_ip_address", models.CharField(max_length=39, null=True, verbose_name=b"Adresse IP", blank=True)),
                ("site", models.CharField(max_length=128, verbose_name=b"Site internet", blank=True)),
                ("show_email", models.BooleanField(default=False, verbose_name=b"Afficher adresse mail publiquement")),
                (
                    "avatar_url",
                    models.CharField(max_length=128, null=True, verbose_name=b"URL de l'avatar", blank=True),
                ),
                ("biography", models.TextField(verbose_name=b"Biographie", blank=True)),
                ("karma", models.IntegerField(default=0, verbose_name=b"Karma")),
                ("sign", models.TextField(max_length=250, verbose_name=b"Signature", blank=True)),
                ("show_sign", models.BooleanField(default=True, verbose_name=b"Voir les signatures")),
                ("hover_or_click", models.BooleanField(default=False, verbose_name=b"Survol ou click ?")),
                (
                    "email_for_answer",
                    models.BooleanField(default=False, verbose_name=b"Envoyer pour les r\xc3\xa9ponse MP"),
                ),
                ("sdz_tutorial", models.TextField(null=True, verbose_name=b"Identifiant des tutos SdZ", blank=True)),
                ("can_read", models.BooleanField(default=True, verbose_name=b"Possibilit\xc3\xa9 de lire")),
                (
                    "end_ban_read",
                    models.DateTimeField(null=True, verbose_name=b"Fin d'interdiction de lecture", blank=True),
                ),
                ("can_write", models.BooleanField(default=True, verbose_name=b"Possibilit\xc3\xa9 d'\xc3\xa9crire")),
                (
                    "end_ban_write",
                    models.DateTimeField(null=True, verbose_name=b"Fin d'interdiction d'ecrire", blank=True),
                ),
                (
                    "last_visit",
                    models.DateTimeField(null=True, verbose_name=b"Date de derni\xc3\xa8re visite", blank=True),
                ),
                (
                    "user",
                    models.OneToOneField(
                        related_name="profile",
                        verbose_name=b"Utilisateur",
                        to=settings.AUTH_USER_MODEL,
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "verbose_name": "Profil",
                "verbose_name_plural": "Profils",
                "permissions": (("moderation", "Mod\xe9rer un membre"), ("show_ip", "Afficher les IP d'un membre")),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="TokenForgotPassword",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                ("token", models.CharField(max_length=100, db_index=True)),
                ("date_end", models.DateTimeField(verbose_name=b"Date de fin")),
                (
                    "user",
                    models.ForeignKey(
                        verbose_name=b"Utilisateur", to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE
                    ),
                ),
            ],
            options={
                "verbose_name": "Token de mot de passe oubli\xe9",
                "verbose_name_plural": "Tokens de mots de passe oubli\xe9s",
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="TokenRegister",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                ("token", models.CharField(max_length=100, db_index=True)),
                ("date_end", models.DateTimeField(verbose_name=b"Date de fin")),
                (
                    "user",
                    models.ForeignKey(
                        verbose_name=b"Utilisateur", to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE
                    ),
                ),
            ],
            options={
                "verbose_name": "Token d'inscription",
                "verbose_name_plural": "Tokens  d'inscription",
            },
            bases=(models.Model,),
        ),
    ]
