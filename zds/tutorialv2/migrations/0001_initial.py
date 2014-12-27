# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'PublishableContent'
        db.create_table(u'tutorialv2_publishablecontent', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=80)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('source', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('image', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['gallery.Image'], null=True, on_delete=models.SET_NULL, blank=True)),
            ('gallery', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['gallery.Gallery'], null=True, blank=True)),
            ('creation_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('pubdate', self.gf('django.db.models.fields.DateTimeField')(db_index=True, null=True, blank=True)),
            ('update_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('sha_public', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=80, null=True, blank=True)),
            ('sha_beta', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=80, null=True, blank=True)),
            ('sha_validation', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=80, null=True, blank=True)),
            ('sha_draft', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=80, null=True, blank=True)),
            ('licence', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['utils.Licence'], null=True, blank=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=10, db_index=True)),
            ('relative_images_path', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('last_note', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='last_note', null=True, to=orm['tutorialv2.ContentReaction'])),
            ('is_locked', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('js_support', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'tutorialv2', ['PublishableContent'])

        # Adding M2M table for field authors on 'PublishableContent'
        m2m_table_name = db.shorten_name(u'tutorialv2_publishablecontent_authors')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('publishablecontent', models.ForeignKey(orm[u'tutorialv2.publishablecontent'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['publishablecontent_id', 'user_id'])

        # Adding M2M table for field subcategory on 'PublishableContent'
        m2m_table_name = db.shorten_name(u'tutorialv2_publishablecontent_subcategory')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('publishablecontent', models.ForeignKey(orm[u'tutorialv2.publishablecontent'], null=False)),
            ('subcategory', models.ForeignKey(orm[u'utils.subcategory'], null=False))
        ))
        db.create_unique(m2m_table_name, ['publishablecontent_id', 'subcategory_id'])

        # Adding M2M table for field helps on 'PublishableContent'
        m2m_table_name = db.shorten_name(u'tutorialv2_publishablecontent_helps')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('publishablecontent', models.ForeignKey(orm[u'tutorialv2.publishablecontent'], null=False)),
            ('helpwriting', models.ForeignKey(orm[u'utils.helpwriting'], null=False))
        ))
        db.create_unique(m2m_table_name, ['publishablecontent_id', 'helpwriting_id'])

        # Adding model 'ContentReaction'
        db.create_table(u'tutorialv2_contentreaction', (
            (u'comment_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['utils.Comment'], unique=True, primary_key=True)),
            ('related_content', self.gf('django.db.models.fields.related.ForeignKey')(related_name='related_content_note', to=orm['tutorialv2.PublishableContent'])),
        ))
        db.send_create_signal(u'tutorialv2', ['ContentReaction'])

        # Adding model 'ContentRead'
        db.create_table(u'tutorialv2_contentread', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('content', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tutorialv2.PublishableContent'])),
            ('note', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tutorialv2.ContentReaction'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='content_notes_read', to=orm['auth.User'])),
        ))
        db.send_create_signal(u'tutorialv2', ['ContentRead'])

        # Adding model 'Validation'
        db.create_table(u'tutorialv2_validation', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('content', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tutorialv2.PublishableContent'], null=True, blank=True)),
            ('version', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=80, null=True, blank=True)),
            ('date_proposition', self.gf('django.db.models.fields.DateTimeField')(db_index=True)),
            ('comment_authors', self.gf('django.db.models.fields.TextField')()),
            ('validator', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='author_content_validations', null=True, to=orm['auth.User'])),
            ('date_reserve', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('date_validation', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('comment_validator', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('status', self.gf('django.db.models.fields.CharField')(default='PENDING', max_length=10)),
        ))
        db.send_create_signal(u'tutorialv2', ['Validation'])


    def backwards(self, orm):
        # Deleting model 'PublishableContent'
        db.delete_table(u'tutorialv2_publishablecontent')

        # Removing M2M table for field authors on 'PublishableContent'
        db.delete_table(db.shorten_name(u'tutorialv2_publishablecontent_authors'))

        # Removing M2M table for field subcategory on 'PublishableContent'
        db.delete_table(db.shorten_name(u'tutorialv2_publishablecontent_subcategory'))

        # Removing M2M table for field helps on 'PublishableContent'
        db.delete_table(db.shorten_name(u'tutorialv2_publishablecontent_helps'))

        # Deleting model 'ContentReaction'
        db.delete_table(u'tutorialv2_contentreaction')

        # Deleting model 'ContentRead'
        db.delete_table(u'tutorialv2_contentread')

        # Deleting model 'Validation'
        db.delete_table(u'tutorialv2_validation')


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
        u'gallery.gallery': {
            'Meta': {'object_name': 'Gallery'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pubdate': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
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
            'physical': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'pubdate': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '80'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '80', 'null': 'True', 'blank': 'True'}),
            'update': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        u'tutorialv2.contentreaction': {
            'Meta': {'object_name': 'ContentReaction', '_ormbases': [u'utils.Comment']},
            u'comment_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['utils.Comment']", 'unique': 'True', 'primary_key': 'True'}),
            'related_content': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'related_content_note'", 'to': u"orm['tutorialv2.PublishableContent']"})
        },
        u'tutorialv2.contentread': {
            'Meta': {'object_name': 'ContentRead'},
            'content': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tutorialv2.PublishableContent']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'note': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tutorialv2.ContentReaction']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'content_notes_read'", 'to': u"orm['auth.User']"})
        },
        u'tutorialv2.publishablecontent': {
            'Meta': {'object_name': 'PublishableContent'},
            'authors': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.User']", 'db_index': 'True', 'symmetrical': 'False'}),
            'creation_date': ('django.db.models.fields.DateTimeField', [], {}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'gallery': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['gallery.Gallery']", 'null': 'True', 'blank': 'True'}),
            'helps': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['utils.HelpWriting']", 'db_index': 'True', 'symmetrical': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['gallery.Image']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'is_locked': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'js_support': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_note': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'last_note'", 'null': 'True', 'to': u"orm['tutorialv2.ContentReaction']"}),
            'licence': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['utils.Licence']", 'null': 'True', 'blank': 'True'}),
            'pubdate': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'relative_images_path': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'sha_beta': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '80', 'null': 'True', 'blank': 'True'}),
            'sha_draft': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '80', 'null': 'True', 'blank': 'True'}),
            'sha_public': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '80', 'null': 'True', 'blank': 'True'}),
            'sha_validation': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '80', 'null': 'True', 'blank': 'True'}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'subcategory': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['utils.SubCategory']", 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '10', 'db_index': 'True'}),
            'update_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        u'tutorialv2.validation': {
            'Meta': {'object_name': 'Validation'},
            'comment_authors': ('django.db.models.fields.TextField', [], {}),
            'comment_validator': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'content': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tutorialv2.PublishableContent']", 'null': 'True', 'blank': 'True'}),
            'date_proposition': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'date_reserve': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'date_validation': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'PENDING'", 'max_length': '10'}),
            'validator': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'author_content_validations'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'version': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '80', 'null': 'True', 'blank': 'True'})
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
        u'utils.helpwriting': {
            'Meta': {'object_name': 'HelpWriting'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '20'}),
            'tablelabel': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        u'utils.licence': {
            'Meta': {'object_name': 'Licence'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '80'})
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

    complete_apps = ['tutorialv2']