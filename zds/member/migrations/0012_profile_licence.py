# Generated by Django 1.10.7 on 2017-06-21 07:40


from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("utils", "0012_commentedit"),
        ("member", "0011_bannedemailprovider_newemailprovider"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="licence",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="utils.Licence",
                verbose_name="Licence pr\xe9f\xe9r\xe9e",
            ),
        ),
    ]
