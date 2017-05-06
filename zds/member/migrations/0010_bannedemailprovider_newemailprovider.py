# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('member', '0009_profile_show_staff_badge'),
    ]

    operations = [
        migrations.CreateModel(
            name='BannedEmailProvider',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('provider', models.CharField(unique=True, max_length=253, verbose_name='Fournisseur', db_index=True)),
                ('date', models.DateTimeField(db_column='ban_date', auto_now_add=True, verbose_name='Date du bannissement', db_index=True)),
                ('moderator', models.ForeignKey(related_name='banned_providers', verbose_name='Mod\xe9rateur', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Fournisseur banni',
                'verbose_name_plural': 'Fournisseurs bannis',
            },
        ),
        migrations.CreateModel(
            name='NewEmailProvider',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('provider', models.CharField(unique=True, max_length=253, verbose_name='Fournisseur', db_index=True)),
                ('use', models.CharField(max_length=11, choices=[('NEW_ACCOUNT', 'Nouveau compte'), ('EMAIL_EDIT', "\xc9dition de l'adresse e-mail")])),
                ('date', models.DateTimeField(db_column='alert_date', auto_now_add=True, verbose_name="Date de l'alerte", db_index=True)),
                ('user', models.ForeignKey(related_name='new_providers', verbose_name='Utilisateur concern\xe9', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Nouveau fournisseur',
                'verbose_name_plural': 'Nouveaux fournisseurs',
            },
        ),
    ]
