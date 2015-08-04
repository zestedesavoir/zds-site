# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tutorialv2', '0005_auto_20150510_2114'),
    ]

    operations = [
        migrations.CreateModel(
            name='SearchIndexAuthors',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('username', models.CharField(max_length=80, verbose_name=b'Pseudo')),
            ],
            options={
                'verbose_name': 'Author',
                'verbose_name_plural': 'Authors',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SearchIndexContainer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=80, verbose_name=b'Titre')),
                ('url_to_redirect', models.CharField(max_length=400, verbose_name=b'Adresse pour rediriger')),
                ('introduction', models.TextField(null=True, verbose_name=b'Introduction', blank=True)),
                ('conclusion', models.TextField(null=True, verbose_name=b'Conclusion', blank=True)),
                ('level', models.CharField(max_length=80, verbose_name=b'level')),
                ('keywords', models.TextField(verbose_name=b'Mots cl\xc3\xa9s du contenu')),
            ],
            options={
                'verbose_name': 'SearchIndexContainer',
                'verbose_name_plural': 'SearchIndexContainers',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SearchIndexContent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=200, verbose_name=b'Titre')),
                ('description', models.TextField(null=True, verbose_name=b'Description', blank=True)),
                ('pub_date', models.DateTimeField(auto_now_add=True, verbose_name=b'Date de cr\xc3\xa9ation')),
                ('update_date', models.DateTimeField(null=True, verbose_name=b'Date de mise \xc3\xa0 jours', blank=True)),
                ('licence', models.CharField(max_length=80, verbose_name=b'Licence du contenu')),
                ('url_image', models.CharField(max_length=200, null=True, verbose_name=b"L'adresse vers l'image du contenu", blank=True)),
                ('url_to_redirect', models.CharField(max_length=400, verbose_name=b'Adresse pour rediriger')),
                ('introduction', models.TextField(null=True, verbose_name=b'Introduction', blank=True)),
                ('conclusion', models.TextField(null=True, verbose_name=b'Conclusion', blank=True)),
                ('keywords', models.TextField(verbose_name=b'Mots cl\xc3\xa9s du contenu')),
                ('type', models.CharField(max_length=80, verbose_name=b'Type de contenu')),
                ('authors', models.ManyToManyField(to='search.SearchIndexAuthors', verbose_name=b'Authors', db_index=True)),
                ('publishable_content', models.ForeignKey(related_name='search_index_content_publishable_content', on_delete=django.db.models.deletion.SET_NULL, verbose_name=b'content', to='tutorialv2.PublishableContent', null=True, db_index=False)),
            ],
            options={
                'verbose_name': 'SearchIndexContent',
                'verbose_name_plural': 'SearchIndexContents',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SearchIndexExtract',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=80, verbose_name=b'Titre')),
                ('url_to_redirect', models.CharField(max_length=400, verbose_name=b'Adresse pour rediriger')),
                ('extract_content', models.TextField(null=True, verbose_name=b'Contenu', blank=True)),
                ('keywords', models.TextField(verbose_name=b'Mots cl\xc3\xa9s du contenu')),
                ('search_index_content', models.ForeignKey(related_name='extract_search_index_content', verbose_name=b'content', to='search.SearchIndexContent')),
            ],
            options={
                'verbose_name': 'SearchIndexExtract',
                'verbose_name_plural': 'SearchIndexExtracts',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SearchIndexTag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=80, verbose_name=b'Titre')),
            ],
            options={
                'verbose_name': 'Tag',
                'verbose_name_plural': 'Tags',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='searchindexcontent',
            name='tags',
            field=models.ManyToManyField(db_index=True, to='search.SearchIndexTag', null=True, verbose_name=b'Tags', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='searchindexcontainer',
            name='search_index_content',
            field=models.ForeignKey(related_name='container_search_index_content', verbose_name=b'content', to='search.SearchIndexContent'),
            preserve_default=True,
        ),
    ]
