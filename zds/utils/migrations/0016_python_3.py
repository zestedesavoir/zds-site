# Generated by Django 1.10.8 on 2017-10-03 21:29
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('utils', '0015_hat_group'),
    ]

    operations = [
        migrations.AlterField(
            model_name='alert',
            name='author',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='alerts', to=settings.AUTH_USER_MODEL, verbose_name='Auteur'),
        ),
        migrations.AlterField(
            model_name='alert',
            name='moderator',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='solved_alerts', to=settings.AUTH_USER_MODEL, verbose_name='Modérateur'),
        ),
        migrations.AlterField(
            model_name='alert',
            name='pubdate',
            field=models.DateTimeField(db_index=True, verbose_name='Date de création'),
        ),
        migrations.AlterField(
            model_name='alert',
            name='resolve_reason',
            field=models.TextField(blank=True, null=True, verbose_name='Texte de résolution'),
        ),
        migrations.AlterField(
            model_name='alert',
            name='scope',
            field=models.CharField(choices=[('FORUM', 'Forum'), ('CONTENT', 'Contenu'), ('TUTORIAL', 'Tutoriel'), ('ARTICLE', 'Article'), ('OPINION', 'Billet')], db_index=True, max_length=10),
        ),
        migrations.AlterField(
            model_name='alert',
            name='solved',
            field=models.BooleanField(default=False, verbose_name='Est résolue'),
        ),
        migrations.AlterField(
            model_name='alert',
            name='solved_date',
            field=models.DateTimeField(blank=True, db_index=True, null=True, verbose_name='Date de résolution'),
        ),
        migrations.AlterField(
            model_name='alert',
            name='text',
            field=models.TextField(verbose_name="Texte d'alerte"),
        ),
        migrations.AlterField(
            model_name='category',
            name='description',
            field=models.TextField(verbose_name='Description'),
        ),
        migrations.AlterField(
            model_name='category',
            name='title',
            field=models.CharField(max_length=80, unique=True, verbose_name='Titre'),
        ),
        migrations.AlterField(
            model_name='categorysubcategory',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='utils.Category', verbose_name='Catégorie'),
        ),
        migrations.AlterField(
            model_name='categorysubcategory',
            name='is_main',
            field=models.BooleanField(db_index=True, default=True, verbose_name='Est la catégorie principale'),
        ),
        migrations.AlterField(
            model_name='categorysubcategory',
            name='subcategory',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='utils.SubCategory', verbose_name='Sous-Catégorie'),
        ),
        migrations.AlterField(
            model_name='comment',
            name='author',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to=settings.AUTH_USER_MODEL, verbose_name='Auteur'),
        ),
        migrations.AlterField(
            model_name='comment',
            name='dislike',
            field=models.IntegerField(default=0, verbose_name='Dislikes'),
        ),
        migrations.AlterField(
            model_name='comment',
            name='editor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='comments-editor+', to=settings.AUTH_USER_MODEL, verbose_name='Editeur'),
        ),
        migrations.AlterField(
            model_name='comment',
            name='ip_address',
            field=models.CharField(max_length=39, verbose_name="Adresse IP de l'auteur "),
        ),
        migrations.AlterField(
            model_name='comment',
            name='is_visible',
            field=models.BooleanField(default=True, verbose_name='Est visible'),
        ),
        migrations.AlterField(
            model_name='comment',
            name='like',
            field=models.IntegerField(default=0, verbose_name='Likes'),
        ),
        migrations.AlterField(
            model_name='comment',
            name='position',
            field=models.IntegerField(db_index=True, verbose_name='Position'),
        ),
        migrations.AlterField(
            model_name='comment',
            name='pubdate',
            field=models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Date de publication'),
        ),
        migrations.AlterField(
            model_name='comment',
            name='text',
            field=models.TextField(verbose_name='Texte'),
        ),
        migrations.AlterField(
            model_name='comment',
            name='text_hidden',
            field=models.CharField(default='', max_length=80, verbose_name='Texte de masquage '),
        ),
        migrations.AlterField(
            model_name='comment',
            name='text_html',
            field=models.TextField(verbose_name='Texte en Html'),
        ),
        migrations.AlterField(
            model_name='comment',
            name='update',
            field=models.DateTimeField(blank=True, null=True, verbose_name="Date d'édition"),
        ),
        migrations.AlterField(
            model_name='comment',
            name='update_index_date',
            field=models.DateTimeField(auto_now=True, db_index=True, verbose_name='Date de dernière modification pour la réindexation partielle'),
        ),
        migrations.AlterField(
            model_name='commentvote',
            name='positive',
            field=models.BooleanField(default=True, verbose_name='Est un vote positif'),
        ),
        migrations.AlterField(
            model_name='helpwriting',
            name='tablelabel',
            field=models.CharField(max_length=150, verbose_name='TableLabel'),
        ),
        migrations.AlterField(
            model_name='helpwriting',
            name='title',
            field=models.CharField(max_length=20, verbose_name='Name'),
        ),
        migrations.AlterField(
            model_name='licence',
            name='code',
            field=models.CharField(max_length=20, verbose_name='Code'),
        ),
        migrations.AlterField(
            model_name='licence',
            name='description',
            field=models.TextField(verbose_name='Description'),
        ),
        migrations.AlterField(
            model_name='licence',
            name='title',
            field=models.CharField(max_length=80, verbose_name='Titre'),
        ),
        migrations.AlterField(
            model_name='subcategory',
            name='subtitle',
            field=models.CharField(max_length=200, verbose_name='Sous-titre'),
        ),
        migrations.AlterField(
            model_name='subcategory',
            name='title',
            field=models.CharField(max_length=80, unique=True, verbose_name='Titre'),
        ),
        migrations.AlterField(
            model_name='tag',
            name='title',
            field=models.CharField(db_index=True, max_length=30, unique=True, verbose_name='Titre'),
        ),
    ]
