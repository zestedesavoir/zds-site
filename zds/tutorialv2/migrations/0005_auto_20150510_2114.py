from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tutorialv2", "0004_publishablecontent_public_version"),
    ]

    operations = [
        migrations.AddField(
            model_name="publishedcontent",
            name="must_redirect",
            field=models.BooleanField(
                default=False, db_index=True, verbose_name=b"Redirection vers  une version plus r\xc3\xa9cente"
            ),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name="validation",
            name="status",
            field=models.CharField(
                default=b"PENDING",
                max_length=10,
                choices=[
                    (b"PENDING", "En attente d'un validateur"),
                    (b"PENDING_V", "En cours de validation"),
                    (b"ACCEPT", "Publi\xe9"),
                    (b"REJECT", "Rejet\xe9"),
                    (b"CANCEL", "Annul\xe9"),
                ],
            ),
            preserve_default=True,
        ),
    ]
