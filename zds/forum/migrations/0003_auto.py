# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding M2M table for field tags on 'Topic'
        m2m_table_name = db.shorten_name(u'forum_topic_tags')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('topic', models.ForeignKey(orm[u'forum.topic'], null=False)),
            ('tag', models.ForeignKey(orm[u'utils.tag'], null=False))
        ))
        db.create_unique(m2m_table_name, ['topic_id', 'tag_id'])


    def backwards(self, orm):
        # Removing M2M table for field tags on 'Topic'
        db.delete_table(db.shorten_name(u'forum_topic_tags'))


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
        u'forum.category': {
            'Meta': {'object_name': 'Category'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'position': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '80'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '80'})
        },
        u'forum.forum': {
            'Meta': {'object_name': 'Forum'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['forum.Category']"}),
            'group': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['auth.Group']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'position_in_category': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '80'}),
            'subtitle': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '80'})
        },
        u'forum.post': {
            'Meta': {'object_name': 'Post', '_ormbases': [u'utils.Comment']},
            u'comment_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['utils.Comment']", 'unique': 'True', 'primary_key': 'True'}),
            'is_useful': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'topic': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['forum.Topic']"})
        },
        u'forum.topic': {
            'Meta': {'object_name': 'Topic'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'topics'", 'to': u"orm['auth.User']"}),
            'forum': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['forum.Forum']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_locked': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_solved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_sticky': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_message': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'last_message'", 'null': 'True', 'to': u"orm['forum.Post']"}),
            'pubdate': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'subtitle': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['utils.Tag']", 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '80'})
        },
        u'forum.topicfollowed': {
            'Meta': {'object_name': 'TopicFollowed'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'topic': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['forum.Topic']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'topics_followed'", 'to': u"orm['auth.User']"})
        },
        u'forum.topicread': {
            'Meta': {'object_name': 'TopicRead'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'post': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['forum.Post']"}),
            'topic': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['forum.Topic']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'topics_read'", 'to': u"orm['auth.User']"})
        },
        u'utils.comment': {
            'Meta': {'object_name': 'Comment'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'comments'", 'to': u"orm['auth.User']"}),
            'dislike': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'editor': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'comments-editor'", 'null': 'True', 'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip_address': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'is_visible': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'like': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'position': ('django.db.models.fields.IntegerField', [], {}),
            'pubdate': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'text_hidden': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '80'}),
            'text_html': ('django.db.models.fields.TextField', [], {}),
            'update': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        u'utils.tag': {
            'Meta': {'object_name': 'Tag'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        }
    }

    complete_apps = ['forum']