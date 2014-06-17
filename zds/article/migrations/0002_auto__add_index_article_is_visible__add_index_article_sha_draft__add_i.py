# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding index on 'Article', fields ['is_visible']
        db.create_index(u'article_article', ['is_visible'])

        # Adding index on 'Article', fields ['sha_draft']
        db.create_index(u'article_article', ['sha_draft'])

        # Adding index on 'Article', fields ['pubdate']
        db.create_index(u'article_article', ['pubdate'])

        # Adding index on 'Article', fields ['sha_validation']
        db.create_index(u'article_article', ['sha_validation'])

        # Adding index on 'Article', fields ['sha_public']
        db.create_index(u'article_article', ['sha_public'])

        # Adding index on 'Validation', fields ['version']
        db.create_index(u'article_validation', ['version'])

        # Adding index on 'Validation', fields ['date_proposition']
        db.create_index(u'article_validation', ['date_proposition'])


    def backwards(self, orm):
        # Removing index on 'Validation', fields ['date_proposition']
        db.delete_index(u'article_validation', ['date_proposition'])

        # Removing index on 'Validation', fields ['version']
        db.delete_index(u'article_validation', ['version'])

        # Removing index on 'Article', fields ['sha_public']
        db.delete_index(u'article_article', ['sha_public'])

        # Removing index on 'Article', fields ['sha_validation']
        db.delete_index(u'article_article', ['sha_validation'])

        # Removing index on 'Article', fields ['pubdate']
        db.delete_index(u'article_article', ['pubdate'])

        # Removing index on 'Article', fields ['sha_draft']
        db.delete_index(u'article_article', ['sha_draft'])

        # Removing index on 'Article', fields ['is_visible']
        db.delete_index(u'article_article', ['is_visible'])


    models = {
        u'article.article': {
            'Meta': {'object_name': 'Article'},
            'authors': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.User']", 'db_index': 'True', 'symmetrical': 'False'}),
            'create_at': ('django.db.models.fields.DateTimeField', [], {}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'is_locked': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_visible': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'last_reaction': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'last_reaction'", 'null': 'True', 'to': u"orm['article.Reaction']"}),
            'pubdate': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'sha_draft': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '80', 'null': 'True', 'blank': 'True'}),
            'sha_public': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '80', 'null': 'True', 'blank': 'True'}),
            'sha_validation': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '80', 'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '80'}),
            'subcategory': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['utils.SubCategory']", 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'text': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'thumbnail': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'update': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        u'article.articleread': {
            'Meta': {'object_name': 'ArticleRead'},
            'article': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['article.Article']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'reaction': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['article.Reaction']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'reactions_read'", 'to': u"orm['auth.User']"})
        },
        u'article.reaction': {
            'Meta': {'object_name': 'Reaction', '_ormbases': [u'utils.Comment']},
            'article': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['article.Article']"}),
            u'comment_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['utils.Comment']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'article.validation': {
            'Meta': {'object_name': 'Validation'},
            'article': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['article.Article']", 'null': 'True', 'blank': 'True'}),
            'comment_authors': ('django.db.models.fields.TextField', [], {}),
            'comment_validator': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'date_proposition': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'date_reserve': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'date_validation': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'PENDING'", 'max_length': '10'}),
            'validator': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'articles_author_validations'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'version': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '80', 'null': 'True', 'blank': 'True'})
        },
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'utils.comment': {
            'Meta': {'object_name': 'Comment'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'comments'", 'to': u"orm['auth.User']"}),
            'dislike': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'editor': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'comments-editor'", 'null': 'True', 'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip_address': ('django.db.models.fields.CharField', [], {'max_length': '39'}),
            'is_visible': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'like': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'position': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'pubdate': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'text_hidden': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '80'}),
            'text_html': ('django.db.models.fields.TextField', [], {}),
            'update': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        u'utils.subcategory': {
            'Meta': {'object_name': 'SubCategory'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '80'}),
            'subtitle': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '80'})
        }
    }

    complete_apps = ['article']