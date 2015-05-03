# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('utils', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('gallery', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Chapter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('position_in_part', models.IntegerField(db_index=True, null=True, verbose_name=b'Position dans la partie', blank=True)),
                ('position_in_tutorial', models.IntegerField(null=True, verbose_name=b'Position dans le tutoriel', blank=True)),
                ('title', models.CharField(max_length=80, verbose_name=b'Titre', blank=True)),
                ('slug', models.SlugField(max_length=80)),
                ('introduction', models.CharField(max_length=200, null=True, verbose_name=b'chemin relatif introduction', blank=True)),
                ('conclusion', models.CharField(max_length=200, null=True, verbose_name=b'chemin relatif conclusion', blank=True)),
                ('image', models.ForeignKey(verbose_name=b'Image du chapitre', blank=True, to='gallery.Image', null=True)),
            ],
            options={
                'verbose_name': 'Chapitre',
                'verbose_name_plural': 'Chapitres',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Extract',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=80, verbose_name=b'Titre')),
                ('position_in_chapter', models.IntegerField(verbose_name=b'Position dans le chapitre', db_index=True)),
                ('text', models.CharField(max_length=200, null=True, verbose_name=b'chemin relatif du texte', blank=True)),
                ('chapter', models.ForeignKey(verbose_name=b'Chapitre parent', to='tutorial.Chapter')),
            ],
            options={
                'verbose_name': 'Extrait',
                'verbose_name_plural': 'Extraits',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Note',
            fields=[
                ('comment_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='utils.Comment')),
            ],
            options={
                'verbose_name': 'note sur un tutoriel',
                'verbose_name_plural': 'notes sur un tutoriel',
            },
            bases=('utils.comment',),
        ),
        migrations.CreateModel(
            name='Part',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('position_in_tutorial', models.IntegerField(verbose_name=b'Position dans le tutoriel', db_index=True)),
                ('title', models.CharField(max_length=80, verbose_name=b'Titre')),
                ('slug', models.SlugField(max_length=80)),
                ('introduction', models.CharField(max_length=200, null=True, verbose_name=b'chemin relatif introduction', blank=True)),
                ('conclusion', models.CharField(max_length=200, null=True, verbose_name=b'chemin relatif conclusion', blank=True)),
            ],
            options={
                'verbose_name': 'Partie',
                'verbose_name_plural': 'Parties',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Tutorial',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=80, verbose_name=b'Titre')),
                ('description', models.CharField(max_length=200, verbose_name=b'Description')),
                ('source', models.CharField(max_length=200, verbose_name=b'Source')),
                ('slug', models.SlugField(max_length=80)),
                ('create_at', models.DateTimeField(verbose_name=b'Date de cr\xc3\xa9ation')),
                ('pubdate', models.DateTimeField(db_index=True, null=True, verbose_name=b'Date de publication', blank=True)),
                ('update', models.DateTimeField(null=True, verbose_name=b'Date de mise \xc3\xa0 jour', blank=True)),
                ('sha_public', models.CharField(db_index=True, max_length=80, null=True, verbose_name=b'Sha1 de la version publique', blank=True)),
                ('sha_beta', models.CharField(db_index=True, max_length=80, null=True, verbose_name=b'Sha1 de la version beta publique', blank=True)),
                ('sha_validation', models.CharField(db_index=True, max_length=80, null=True, verbose_name=b'Sha1 de la version en validation', blank=True)),
                ('sha_draft', models.CharField(db_index=True, max_length=80, null=True, verbose_name=b'Sha1 de la version de r\xc3\xa9daction', blank=True)),
                ('type', models.CharField(db_index=True, max_length=10, choices=[(b'MINI', b'Mini-tuto'), (b'BIG', b'Big-tuto')])),
                ('introduction', models.CharField(max_length=200, null=True, verbose_name=b'chemin relatif introduction', blank=True)),
                ('conclusion', models.CharField(max_length=200, null=True, verbose_name=b'chemin relatif conclusion', blank=True)),
                ('images', models.CharField(max_length=200, null=True, verbose_name=b'chemin relatif images', blank=True)),
                ('is_locked', models.BooleanField(default=False, verbose_name=b'Est verrouill\xc3\xa9')),
                ('js_support', models.BooleanField(default=False, verbose_name=b'Support du Javascript')),
                ('authors', models.ManyToManyField(to=settings.AUTH_USER_MODEL, verbose_name=b'Auteurs', db_index=True)),
                ('gallery', models.ForeignKey(verbose_name=b"Galerie d'images", blank=True, to='gallery.Gallery', null=True)),
                ('helps', models.ManyToManyField(to='utils.HelpWriting', verbose_name=b'Aides', db_index=True)),
                ('image', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name=b'Image du tutoriel', blank=True, to='gallery.Image', null=True)),
                ('last_note', models.ForeignKey(related_name='last_note', verbose_name=b'Derniere note', blank=True, to='tutorial.Note', null=True)),
                ('licence', models.ForeignKey(verbose_name=b'Licence', blank=True, to='utils.Licence', null=True)),
                ('subcategory', models.ManyToManyField(db_index=True, to='utils.SubCategory', null=True, verbose_name=b'Sous-Cat\xc3\xa9gorie', blank=True)),
            ],
            options={
                'verbose_name': 'Tutoriel',
                'verbose_name_plural': 'Tutoriels',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TutorialRead',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('note', models.ForeignKey(to='tutorial.Note')),
                ('tutorial', models.ForeignKey(to='tutorial.Tutorial')),
                ('user', models.ForeignKey(related_name='tuto_notes_read', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Tutoriel lu',
                'verbose_name_plural': 'Tutoriels lus',
            },
            bases=(models.Model,),
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
                ('status', models.CharField(default=b'PENDING', max_length=10, choices=[(b'PENDING', b"En attente d'un validateur"), (b'PENDING_V', b'En cours de validation'), (b'ACCEPT', b'Publi\xc3\xa9'), (b'REJECT', b'Rejet\xc3\xa9')])),
                ('tutorial', models.ForeignKey(verbose_name=b'Tutoriel propos\xc3\xa9', blank=True, to='tutorial.Tutorial', null=True)),
                ('validator', models.ForeignKey(related_name='author_validations', verbose_name=b'Validateur', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'verbose_name': 'Validation',
                'verbose_name_plural': 'Validations',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='part',
            name='tutorial',
            field=models.ForeignKey(verbose_name=b'Tutoriel parent', to='tutorial.Tutorial'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='note',
            name='tutorial',
            field=models.ForeignKey(verbose_name=b'Tutoriel', to='tutorial.Tutorial'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='chapter',
            name='part',
            field=models.ForeignKey(verbose_name=b'Partie parente', blank=True, to='tutorial.Part', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='chapter',
            name='tutorial',
            field=models.ForeignKey(verbose_name=b'Tutoriel parent', blank=True, to='tutorial.Tutorial', null=True),
            preserve_default=True,
        ),
    ]
