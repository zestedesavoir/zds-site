# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2017-10-03 21:29
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0003_auto_20150928_1249'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gallery',
            name='title',
            field=models.CharField(max_length=80, verbose_name='Titre'),
        ),
        migrations.AlterField(
            model_name='gallery',
            name='update',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Date de modification'),
        ),
        migrations.AlterField(
            model_name='image',
            name='gallery',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gallery.Gallery', verbose_name='Galerie'),
        ),
        migrations.AlterField(
            model_name='image',
            name='update',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Date de modification'),
        ),
        migrations.AlterField(
            model_name='usergallery',
            name='gallery',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gallery.Gallery', verbose_name='Galerie'),
        ),
        migrations.AlterField(
            model_name='usergallery',
            name='mode',
            field=models.CharField(choices=[('R', 'Lecture'), ('W', 'Écriture')], default='R', max_length=1),
        ),
        migrations.AlterField(
            model_name='usergallery',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Membre'),
        ),
    ]
