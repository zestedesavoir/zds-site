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
            ('pubdate', self.gf('django.db.models.fields.DateTimeField')(blank=True)),
            ('update', self.gf('django.db.models.fields.DateTimeField')(blank=True)),
        ))
        db.send_create_signal(u'utils', ['DateManager'])


    def backwards(self, orm):
        # Deleting model 'DateManager'
        db.delete_table(u'utils_datemanager')


    models = {
        u'utils.datemanager': {
            'Meta': {'object_name': 'DateManager'},
            'create_at': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pubdate': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'update': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'})
        }
    }

    complete_apps = ['utils']