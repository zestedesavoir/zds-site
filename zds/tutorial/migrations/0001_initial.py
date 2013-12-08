# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Tutorial'
        db.create_table(u'tutorial_tutorial', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=80)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=80)),
            ('image', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['gallery.Image'], null=True, blank=True)),
            ('create_at', self.gf('django.db.models.fields.DateTimeField')()),
            ('pubdate', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('update', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('sha_public', self.gf('django.db.models.fields.CharField')(max_length=80, null=True, blank=True)),
            ('sha_beta', self.gf('django.db.models.fields.CharField')(max_length=80, null=True, blank=True)),
            ('sha_validation', self.gf('django.db.models.fields.CharField')(max_length=80, null=True, blank=True)),
            ('sha_draft', self.gf('django.db.models.fields.CharField')(max_length=80, null=True, blank=True)),
            ('licence', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['utils.Licence'], null=True, blank=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=10)),
        ))
        db.send_create_signal(u'tutorial', ['Tutorial'])

        # Adding M2M table for field authors on 'Tutorial'
        m2m_table_name = db.shorten_name(u'tutorial_tutorial_authors')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('tutorial', models.ForeignKey(orm[u'tutorial.tutorial'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['tutorial_id', 'user_id'])

        # Adding M2M table for field category on 'Tutorial'
        m2m_table_name = db.shorten_name(u'tutorial_tutorial_category')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('tutorial', models.ForeignKey(orm[u'tutorial.tutorial'], null=False)),
            ('category', models.ForeignKey(orm[u'utils.category'], null=False))
        ))
        db.create_unique(m2m_table_name, ['tutorial_id', 'category_id'])

        # Adding model 'Part'
        db.create_table(u'tutorial_part', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('tutorial', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tutorial.Tutorial'])),
            ('position_in_tutorial', self.gf('django.db.models.fields.IntegerField')()),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=80)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=80)),
        ))
        db.send_create_signal(u'tutorial', ['Part'])

        # Adding model 'Chapter'
        db.create_table(u'tutorial_chapter', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('part', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tutorial.Part'], null=True, blank=True)),
            ('position_in_part', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('image', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['gallery.Image'], null=True, blank=True)),
            ('position_in_tutorial', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('tutorial', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tutorial.Tutorial'], null=True, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=80, blank=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=80)),
        ))
        db.send_create_signal(u'tutorial', ['Chapter'])

        # Adding model 'Extract'
        db.create_table(u'tutorial_extract', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=80)),
            ('chapter', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tutorial.Chapter'])),
            ('position_in_chapter', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal(u'tutorial', ['Extract'])

        # Adding model 'Validation'
        db.create_table(u'tutorial_validation', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('tutorial', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tutorial.Tutorial'], null=True, blank=True)),
            ('date_proposition', self.gf('django.db.models.fields.DateTimeField')()),
            ('comment_authors', self.gf('django.db.models.fields.TextField')()),
            ('validator', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='author_validations', null=True, to=orm['auth.User'])),
            ('date_validation', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('comment_validator', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('status', self.gf('django.db.models.fields.CharField')(default='PENDING', max_length=10)),
        ))
        db.send_create_signal(u'tutorial', ['Validation'])


    def backwards(self, orm):
        # Deleting model 'Tutorial'
        db.delete_table(u'tutorial_tutorial')

        # Removing M2M table for field authors on 'Tutorial'
        db.delete_table(db.shorten_name(u'tutorial_tutorial_authors'))

        # Removing M2M table for field category on 'Tutorial'
        db.delete_table(db.shorten_name(u'tutorial_tutorial_category'))

        # Deleting model 'Part'
        db.delete_table(u'tutorial_part')

        # Deleting model 'Chapter'
        db.delete_table(u'tutorial_chapter')

        # Deleting model 'Extract'
        db.delete_table(u'tutorial_extract')

        # Deleting model 'Validation'
        db.delete_table(u'tutorial_validation')


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
        u'gallery.gallery': {
            'Meta': {'object_name': 'Gallery'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pubdate': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '80'}),
            'subtitle': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'update': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        u'gallery.image': {
            'Meta': {'object_name': 'Image'},
            'gallery': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['gallery.Gallery']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'legend': ('django.db.models.fields.CharField', [], {'max_length': '80', 'null': 'True', 'blank': 'True'}),
            'medium': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'physical': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'pubdate': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '80'}),
            'thumb': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '80', 'null': 'True', 'blank': 'True'}),
            'update': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        u'tutorial.chapter': {
            'Meta': {'object_name': 'Chapter'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['gallery.Image']", 'null': 'True', 'blank': 'True'}),
            'part': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tutorial.Part']", 'null': 'True', 'blank': 'True'}),
            'position_in_part': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'position_in_tutorial': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '80'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '80', 'blank': 'True'}),
            'tutorial': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tutorial.Tutorial']", 'null': 'True', 'blank': 'True'})
        },
        u'tutorial.extract': {
            'Meta': {'object_name': 'Extract'},
            'chapter': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tutorial.Chapter']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'position_in_chapter': ('django.db.models.fields.IntegerField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '80'})
        },
        u'tutorial.part': {
            'Meta': {'object_name': 'Part'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'position_in_tutorial': ('django.db.models.fields.IntegerField', [], {}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '80'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'tutorial': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tutorial.Tutorial']"})
        },
        u'tutorial.tutorial': {
            'Meta': {'object_name': 'Tutorial'},
            'authors': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.User']", 'symmetrical': 'False'}),
            'category': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['utils.Category']", 'null': 'True', 'blank': 'True'}),
            'create_at': ('django.db.models.fields.DateTimeField', [], {}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['gallery.Image']", 'null': 'True', 'blank': 'True'}),
            'licence': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['utils.Licence']", 'null': 'True', 'blank': 'True'}),
            'pubdate': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'sha_beta': ('django.db.models.fields.CharField', [], {'max_length': '80', 'null': 'True', 'blank': 'True'}),
            'sha_draft': ('django.db.models.fields.CharField', [], {'max_length': '80', 'null': 'True', 'blank': 'True'}),
            'sha_public': ('django.db.models.fields.CharField', [], {'max_length': '80', 'null': 'True', 'blank': 'True'}),
            'sha_validation': ('django.db.models.fields.CharField', [], {'max_length': '80', 'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '80'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'update': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        u'tutorial.validation': {
            'Meta': {'object_name': 'Validation'},
            'comment_authors': ('django.db.models.fields.TextField', [], {}),
            'comment_validator': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'date_proposition': ('django.db.models.fields.DateTimeField', [], {}),
            'date_validation': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'PENDING'", 'max_length': '10'}),
            'tutorial': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tutorial.Tutorial']", 'null': 'True', 'blank': 'True'}),
            'validator': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'author_validations'", 'null': 'True', 'to': u"orm['auth.User']"})
        },
        u'utils.category': {
            'Meta': {'ordering': "('title',)", 'object_name': 'Category'},
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '80'})
        },
        u'utils.licence': {
            'Meta': {'object_name': 'Licence'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '80'})
        }
    }

    complete_apps = ['tutorial']