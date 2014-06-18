# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding index on 'PrivatePost', fields ['position_in_topic']
        db.create_index(u'mp_privatepost', ['position_in_topic'])

        # Adding index on 'PrivatePost', fields ['pubdate']
        db.create_index(u'mp_privatepost', ['pubdate'])

        # Adding index on 'PrivateTopic', fields ['pubdate']
        db.create_index(u'mp_privatetopic', ['pubdate'])


    def backwards(self, orm):
        # Removing index on 'PrivateTopic', fields ['pubdate']
        db.delete_index(u'mp_privatetopic', ['pubdate'])

        # Removing index on 'PrivatePost', fields ['pubdate']
        db.delete_index(u'mp_privatepost', ['pubdate'])

        # Removing index on 'PrivatePost', fields ['position_in_topic']
        db.delete_index(u'mp_privatepost', ['position_in_topic'])


    models = {
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
        u'mp.privatepost': {
            'Meta': {'object_name': 'PrivatePost'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'privateposts'", 'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'position_in_topic': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'privatetopic': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mp.PrivateTopic']"}),
            'pubdate': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'text_html': ('django.db.models.fields.TextField', [], {}),
            'update': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        u'mp.privatetopic': {
            'Meta': {'object_name': 'PrivateTopic'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'author'", 'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_message': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'last_message'", 'null': 'True', 'to': u"orm['mp.PrivatePost']"}),
            'participants': ('django.db.models.fields.related.ManyToManyField', [], {'db_index': 'True', 'related_name': "'participants'", 'symmetrical': 'False', 'to': u"orm['auth.User']"}),
            'pubdate': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'subtitle': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '80'})
        },
        u'mp.privatetopicread': {
            'Meta': {'object_name': 'PrivateTopicRead'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'privatepost': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mp.PrivatePost']"}),
            'privatetopic': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mp.PrivateTopic']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'privatetopics_read'", 'to': u"orm['auth.User']"})
        }
    }

    complete_apps = ['mp']