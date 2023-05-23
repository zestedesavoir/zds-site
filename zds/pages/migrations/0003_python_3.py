# Generated by Django 1.10.8 on 2017-10-03 21:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("pages", "0002_auto_20170831_1023"),
    ]

    operations = [
        migrations.AlterField(
            model_name="groupcontact",
            name="description",
            field=models.TextField(blank=True, null=True, verbose_name="Description (en markdown)"),
        ),
        migrations.AlterField(
            model_name="groupcontact",
            name="email",
            field=models.EmailField(blank=True, max_length=254, null=True, verbose_name="Adresse mail du groupe"),
        ),
        migrations.AlterField(
            model_name="groupcontact",
            name="group",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE, to="auth.Group", verbose_name="Groupe d'utilisateur"
            ),
        ),
        migrations.AlterField(
            model_name="groupcontact",
            name="name",
            field=models.CharField(max_length=32, unique=True, verbose_name="Nom (ex: Le staff)"),
        ),
        migrations.AlterField(
            model_name="groupcontact",
            name="position",
            field=models.PositiveSmallIntegerField(unique=True, verbose_name="Position dans la page"),
        ),
    ]
