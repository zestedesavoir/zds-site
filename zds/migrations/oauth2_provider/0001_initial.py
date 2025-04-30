import oauth2_provider.generators
import oauth2_provider.validators
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AccessToken",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                ("token", models.CharField(max_length=255, db_index=True)),
                ("expires", models.DateTimeField()),
                ("scope", models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name="Application",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                (
                    "client_id",
                    models.CharField(
                        default=oauth2_provider.generators.generate_client_id,
                        unique=True,
                        max_length=100,
                        db_index=True,
                    ),
                ),
                (
                    "redirect_uris",
                    models.TextField(
                        help_text="Allowed URIs list, space separated",
                        blank=True,
                        validators=[oauth2_provider.validators.validate_uris],
                    ),
                ),
                (
                    "client_type",
                    models.CharField(max_length=32, choices=[("confidential", "Confidential"), ("public", "Public")]),
                ),
                (
                    "authorization_grant_type",
                    models.CharField(
                        max_length=32,
                        choices=[
                            ("authorization-code", "Authorization code"),
                            ("implicit", "Implicit"),
                            ("password", "Resource owner password-based"),
                            ("client-credentials", "Client credentials"),
                        ],
                    ),
                ),
                (
                    "client_secret",
                    models.CharField(
                        default=oauth2_provider.generators.generate_client_secret,
                        max_length=255,
                        db_index=True,
                        blank=True,
                    ),
                ),
                ("name", models.CharField(max_length=255, blank=True)),
                ("skip_authorization", models.BooleanField(default=False)),
                ("user", models.ForeignKey(related_name="oauth2_provider_application", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Grant",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                ("code", models.CharField(max_length=255, db_index=True)),
                ("expires", models.DateTimeField()),
                ("redirect_uri", models.CharField(max_length=255)),
                ("scope", models.TextField(blank=True)),
                ("application", models.ForeignKey(to=settings.OAUTH2_PROVIDER_APPLICATION_MODEL)),
                ("user", models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="RefreshToken",
            fields=[
                ("id", models.AutoField(verbose_name="ID", serialize=False, auto_created=True, primary_key=True)),
                ("token", models.CharField(max_length=255, db_index=True)),
                ("access_token", models.OneToOneField(related_name="refresh_token", to="oauth2_provider.AccessToken")),
                ("application", models.ForeignKey(to=settings.OAUTH2_PROVIDER_APPLICATION_MODEL)),
                ("user", models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name="accesstoken",
            name="application",
            field=models.ForeignKey(to=settings.OAUTH2_PROVIDER_APPLICATION_MODEL),
        ),
        migrations.AddField(
            model_name="accesstoken",
            name="user",
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
