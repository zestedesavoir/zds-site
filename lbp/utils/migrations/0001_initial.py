# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'DateManager'
        db.create_table(u'utils_datemanager', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('create_at', self.gf('django.db.models.fields.DateTimeField')(blank=True)),
            ('pubdate', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('update', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'utils', ['DateManager'])

        # Adding model 'Alert'
        db.create_table(u'utils_alert', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('text', self.gf('django.db.models.fields.TextField')()),
            ('pubdate', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'utils', ['Alert'])

        # Adding model 'Version'
        db.create_table(u'utils_version', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('public_version_number', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('beta_version_number', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('beta_version_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('validation_version_number', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('validation_version_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('draft_version_number', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal(u'utils', ['Version'])

        # Adding model 'Category'
        db.create_table(u'utils_category', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=80)),
            ('description', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'utils', ['Category'])

        # Adding model 'Licence'
        db.create_table(u'utils_licence', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=80)),
            ('description', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'utils', ['Licence'])


    def backwards(self, orm):
        # Deleting model 'DateManager'
        db.delete_table(u'utils_datemanager')

        # Deleting model 'Alert'
        db.delete_table(u'utils_alert')

        # Deleting model 'Version'
        db.delete_table(u'utils_version')

        # Deleting model 'Category'
        db.delete_table(u'utils_category')

        # Deleting model 'Licence'
        db.delete_table(u'utils_licence')


    models = {
        u'utils.alert': {
            'Meta': {'object_name': 'Alert'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pubdate': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {})
        },
        u'utils.category': {
            'Meta': {'ordering': "('title',)", 'object_name': 'Category'},
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '80'})
        },
        u'utils.datemanager': {
            'Meta': {'object_name': 'DateManager'},
            'create_at': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pubdate': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'update': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        u'utils.licence': {
            'Meta': {'object_name': 'Licence'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '80'})
        },
        u'utils.version': {
            'Meta': {'object_name': 'Version'},
            'beta_version_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'beta_version_number': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'draft_version_number': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'public_version_number': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'validation_version_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'validation_version_number': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        }
    }

    complete_apps = ['utils']