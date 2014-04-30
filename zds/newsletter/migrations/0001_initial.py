# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Newsletter'
        db.create_table(u'newsletter_newsletter', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('email', self.gf('django.db.models.fields.CharField')(max_length=80)),
            ('ip', self.gf('django.db.models.fields.CharField')(max_length=20)),
        ))
        db.send_create_signal(u'newsletter', ['Newsletter'])


    def backwards(self, orm):
        # Deleting model 'Newsletter'
        db.delete_table(u'newsletter_newsletter')


    models = {
        u'newsletter.newsletter': {
            'Meta': {'object_name': 'Newsletter'},
            'email': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        }
    }

    complete_apps = ['newsletter']