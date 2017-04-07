# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tutorialv2', '0021_picklistoperation'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='picklistoperation',
            options={'verbose_name': "Choix d'un billet", 'verbose_name_plural': 'Choix des billets'},
        ),
        migrations.AddField(
            model_name='picklistoperation',
            name='canceler_user',
            field=models.ForeignKey(related_name='canceled_pick_operations', on_delete=django.db.models.deletion.SET_NULL, verbose_name='Mod\xe9rateur qui a annul\xe9 la d\xe9cision', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterField(
            model_name='picklistoperation',
            name='content',
            field=models.ForeignKey(verbose_name='Contenu propos\xe9', to='tutorialv2.PublishableContent'),
        ),
        migrations.AlterField(
            model_name='picklistoperation',
            name='operation',
            field=models.CharField(db_index=True, max_length=10, choices=[('REJECT', 'Rejet\xe9'), ('NO_PICK', 'Non choisi'), ('PICK', 'Choisi'), ('REMOVE_PUB', 'D\xe9publier d\xe9finitivement')]),
        ),
        migrations.AlterField(
            model_name='picklistoperation',
            name='operation_date',
            field=models.DateTimeField(verbose_name="Date de l'op\xe9ration", db_index=True),
        ),
        migrations.AlterField(
            model_name='picklistoperation',
            name='staff_user',
            field=models.ForeignKey(related_name='pick_operations', on_delete=django.db.models.deletion.SET_NULL, verbose_name='Mod\xe9rateur', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterField(
            model_name='picklistoperation',
            name='version',
            field=models.CharField(max_length=128, verbose_name='Version du billet concern\xe9e'),
        ),
    ]
