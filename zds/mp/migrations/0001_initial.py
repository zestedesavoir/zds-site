# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'PrivateTopic'
        db.create_table(u'mp_privatetopic', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=80)),
            ('subtitle', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(related_name='author', to=orm['auth.User'])),
            ('last_message', self.gf('django.db.models.fields.related.ForeignKey')(related_name='last_message', null=True, to=orm['mp.PrivatePost'])),
            ('pubdate', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'mp', ['PrivateTopic'])

        # Adding M2M table for field participants on 'PrivateTopic'
        m2m_table_name = db.shorten_name(u'mp_privatetopic_participants')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('privatetopic', models.ForeignKey(orm[u'mp.privatetopic'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['privatetopic_id', 'user_id'])

        # Adding model 'PrivatePost'
        db.create_table(u'mp_privatepost', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('privatetopic', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mp.PrivateTopic'])),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(related_name='privateposts', to=orm['auth.User'])),
            ('text', self.gf('django.db.models.fields.TextField')()),
            ('pubdate', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('update', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('position_in_topic', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal(u'mp', ['PrivatePost'])

        # Adding model 'PrivateTopicRead'
        db.create_table(u'mp_privatetopicread', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('privatetopic', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mp.PrivateTopic'])),
            ('privatepost', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mp.PrivatePost'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='privatetopics_read', to=orm['auth.User'])),
        ))
        db.send_create_signal(u'mp', ['PrivateTopicRead'])


    def backwards(self, orm):
        # Deleting model 'PrivateTopic'
        db.delete_table(u'mp_privatetopic')

        # Removing M2M table for field participants on 'PrivateTopic'
        db.delete_table(db.shorten_name(u'mp_privatetopic_participants'))

        # Deleting model 'PrivatePost'
        db.delete_table(u'mp_privatepost')

        # Deleting model 'PrivateTopicRead'
        db.delete_table(u'mp_privatetopicread')


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
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
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
            'position_in_topic': ('django.db.models.fields.IntegerField', [], {}),
            'privatetopic': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mp.PrivateTopic']"}),
            'pubdate': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'update': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        u'mp.privatetopic': {
            'Meta': {'object_name': 'PrivateTopic'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'author'", 'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_message': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'last_message'", 'null': 'True', 'to': u"orm['mp.PrivatePost']"}),
            'participants': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'participants'", 'symmetrical': 'False', 'to': u"orm['auth.User']"}),
            'pubdate': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
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