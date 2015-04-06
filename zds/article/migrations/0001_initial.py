# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import zds.article.models
import easy_thumbnails.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('utils', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Article',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=80, verbose_name=b'Titre')),
                ('description', models.CharField(max_length=200, verbose_name=b'Description')),
                ('slug', models.SlugField(max_length=80)),
                ('create_at', models.DateTimeField(verbose_name=b'Date de cr\xc3\xa9ation')),
                ('pubdate', models.DateTimeField(db_index=True, null=True, verbose_name=b'Date de publication', blank=True)),
                ('update', models.DateTimeField(null=True, verbose_name=b'Date de mise \xc3\xa0 jour', blank=True)),
                ('image', easy_thumbnails.fields.ThumbnailerImageField(null=True, upload_to=zds.article.models.image_path, blank=True)),
                ('is_visible', models.BooleanField(default=False, db_index=True, verbose_name=b'Visible en r\xc3\xa9daction')),
                ('sha_public', models.CharField(db_index=True, max_length=80, null=True, verbose_name=b'Sha1 de la version publique', blank=True)),
                ('sha_validation', models.CharField(db_index=True, max_length=80, null=True, verbose_name=b'Sha1 de la version en validation', blank=True)),
                ('sha_draft', models.CharField(db_index=True, max_length=80, null=True, verbose_name=b'Sha1 de la version de r\xc3\xa9daction', blank=True)),
                ('text', models.CharField(max_length=200, null=True, verbose_name=b'chemin relatif du texte', blank=True)),
                ('is_locked', models.BooleanField(default=False, verbose_name=b'Est verrouill\xc3\xa9')),
                ('js_support', models.BooleanField(default=False, verbose_name=b'Support du Javascript')),
                ('authors', models.ManyToManyField(to=settings.AUTH_USER_MODEL, verbose_name=b'Auteurs', db_index=True)),
            ],
            options={
                'verbose_name': 'Article',
                'verbose_name_plural': 'Articles',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ArticleRead',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('article', models.ForeignKey(to='article.Article')),
            ],
            options={
                'verbose_name': 'Article lu',
                'verbose_name_plural': 'Articles lus',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Reaction',
            fields=[
                ('comment_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='utils.Comment')),
                ('article', models.ForeignKey(verbose_name=b'Article', to='article.Article')),
            ],
            options={
            },
            bases=('utils.comment',),
        ),
        migrations.CreateModel(
            name='Validation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('version', models.CharField(db_index=True, max_length=80, null=True, verbose_name=b'Sha1 de la version', blank=True)),
                ('date_proposition', models.DateTimeField(verbose_name=b'Date de proposition', db_index=True)),
                ('comment_authors', models.TextField(verbose_name=b"Commentaire de l'auteur")),
                ('date_reserve', models.DateTimeField(null=True, verbose_name=b'Date de r\xc3\xa9servation', blank=True)),
                ('date_validation', models.DateTimeField(null=True, verbose_name=b'Date de validation', blank=True)),
                ('comment_validator', models.TextField(null=True, verbose_name=b'Commentaire du validateur', blank=True)),
                ('status', models.CharField(default=b'PENDING', max_length=10, choices=[(b'PENDING', b"En attente d'un validateur"), (b'RESERVED', b'En cours de validation'), (b'PUBLISHED', b'Publi\xc3\xa9'), (b'REJECTED', b'Rejet\xc3\xa9')])),
                ('article', models.ForeignKey(verbose_name=b'Article propos\xc3\xa9', blank=True, to='article.Article', null=True)),
                ('validator', models.ForeignKey(related_name='articles_author_validations', verbose_name=b'Validateur', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'verbose_name': 'Validation',
                'verbose_name_plural': 'Validations',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='articleread',
            name='reaction',
            field=models.ForeignKey(to='article.Reaction'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='articleread',
            name='user',
            field=models.ForeignKey(related_name='reactions_read', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='article',
            name='last_reaction',
            field=models.ForeignKey(related_name='last_reaction', verbose_name=b'Derniere r\xc3\xa9action', blank=True, to='article.Reaction', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='article',
            name='licence',
            field=models.ForeignKey(verbose_name=b'Licence', blank=True, to='utils.Licence', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='article',
            name='subcategory',
            field=models.ManyToManyField(db_index=True, to='utils.SubCategory', null=True, verbose_name=b'Sous-Cat\xc3\xa9gorie', blank=True),
            preserve_default=True,
        ),
    ]
