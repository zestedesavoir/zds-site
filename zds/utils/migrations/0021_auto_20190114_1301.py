# Generated by Django 2.1.5 on 2019-01-14 13:01

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('utils', '0020_auto_20180501_1059'),
    ]

    operations = [
        migrations.AlterField(
            model_name='alert',
            name='moderator',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='solved_alerts', to=settings.AUTH_USER_MODEL, verbose_name='Modérateur'),
        ),
        migrations.AlterField(
            model_name='comment',
            name='editor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='comments-editor+', to=settings.AUTH_USER_MODEL, verbose_name='Editeur'),
        ),
        migrations.AlterField(
            model_name='commentedit',
            name='deleted_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='deleted_edits', to=settings.AUTH_USER_MODEL, verbose_name='Supprimé par'),
        ),
        migrations.AlterField(
            model_name='hatrequest',
            name='moderator',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Modérateur'),
        ),
    ]
