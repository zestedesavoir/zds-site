# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'Newsletter.ip'
        db.alter_column(u'newsletter_newsletter', 'ip', self.gf('django.db.models.fields.CharField')(max_length=39))

    def backwards(self, orm):

        # Changing field 'Newsletter.ip'
        db.alter_column(u'newsletter_newsletter', 'ip', self.gf('django.db.models.fields.CharField')(max_length=20))

    models = {
        u'newsletter.newsletter': {
            'Meta': {'object_name': 'Newsletter'},
            'email': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip': ('django.db.models.fields.CharField', [], {'max_length': '39'})
        }
    }

    complete_apps = ['newsletter']