# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2017-10-03 21:29
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('member', '0015_auto_20170905_2220'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ban',
            name='moderator',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bans', to=settings.AUTH_USER_MODEL, verbose_name='Moderateur'),
        ),
        migrations.AlterField(
            model_name='ban',
            name='note',
            field=models.TextField(verbose_name='Explication de la sanction'),
        ),
        migrations.AlterField(
            model_name='ban',
            name='pubdate',
            field=models.DateTimeField(blank=True, db_index=True, null=True, verbose_name='Date de publication'),
        ),
        migrations.AlterField(
            model_name='ban',
            name='type',
            field=models.CharField(db_index=True, max_length=80, verbose_name='Type'),
        ),
        migrations.AlterField(
            model_name='ban',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Sanctionné'),
        ),
        migrations.AlterField(
            model_name='karmanote',
            name='karma',
            field=models.IntegerField(verbose_name='Valeur'),
        ),
        migrations.AlterField(
            model_name='karmanote',
            name='note',
            field=models.CharField(max_length=150, verbose_name='Commentaire'),
        ),
        migrations.AlterField(
            model_name='karmanote',
            name='pubdate',
            field=models.DateTimeField(auto_now_add=True, verbose_name="Date d'ajout"),
        ),
        migrations.AlterField(
            model_name='profile',
            name='allow_temp_visual_changes',
            field=models.BooleanField(default=True, verbose_name='Activer les changements visuels temporaires'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='avatar_url',
            field=models.CharField(blank=True, max_length=2000, null=True, verbose_name="URL de l'avatar"),
        ),
        migrations.AlterField(
            model_name='profile',
            name='biography',
            field=models.TextField(blank=True, verbose_name='Biographie'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='can_read',
            field=models.BooleanField(default=True, verbose_name='Possibilité de lire'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='can_write',
            field=models.BooleanField(default=True, verbose_name="Possibilité d'écrire"),
        ),
        migrations.AlterField(
            model_name='profile',
            name='email_for_answer',
            field=models.BooleanField(default=False, verbose_name='Envoyer pour les réponse MP'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='end_ban_read',
            field=models.DateTimeField(blank=True, null=True, verbose_name="Fin d'interdiction de lecture"),
        ),
        migrations.AlterField(
            model_name='profile',
            name='end_ban_write',
            field=models.DateTimeField(blank=True, null=True, verbose_name="Fin d'interdiction d'écrire"),
        ),
        migrations.AlterField(
            model_name='profile',
            name='github_token',
            field=models.TextField(blank=True, verbose_name='GitHub'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='is_hover_enabled',
            field=models.BooleanField(default=False, verbose_name='Déroulement au survol\xa0?'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='karma',
            field=models.IntegerField(default=0, verbose_name='Karma'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='last_ip_address',
            field=models.CharField(blank=True, max_length=39, null=True, verbose_name='Adresse IP'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='last_visit',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Date de dernière visite'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='show_email',
            field=models.BooleanField(default=False, verbose_name='Afficher adresse mail publiquement'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='show_sign',
            field=models.BooleanField(default=True, verbose_name='Voir les signatures'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='sign',
            field=models.TextField(blank=True, max_length=500, verbose_name='Signature'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='site',
            field=models.CharField(blank=True, max_length=2000, verbose_name='Site internet'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='use_old_smileys',
            field=models.BooleanField(default=False, verbose_name='Utilise les anciens smileys\xa0?'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL, verbose_name='Utilisateur'),
        ),
        migrations.AlterField(
            model_name='tokenforgotpassword',
            name='date_end',
            field=models.DateTimeField(verbose_name='Date de fin'),
        ),
        migrations.AlterField(
            model_name='tokenforgotpassword',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Utilisateur'),
        ),
        migrations.AlterField(
            model_name='tokenregister',
            name='date_end',
            field=models.DateTimeField(verbose_name='Date de fin'),
        ),
        migrations.AlterField(
            model_name='tokenregister',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Utilisateur'),
        ),
    ]
