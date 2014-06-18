# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding index on 'Tutorial', fields ['pubdate']
        db.create_index(u'tutorial_tutorial', ['pubdate'])

        # Adding index on 'Tutorial', fields ['sha_public']
        db.create_index(u'tutorial_tutorial', ['sha_public'])

        # Adding index on 'Tutorial', fields ['sha_beta']
        db.create_index(u'tutorial_tutorial', ['sha_beta'])

        # Adding index on 'Tutorial', fields ['sha_validation']
        db.create_index(u'tutorial_tutorial', ['sha_validation'])

        # Adding index on 'Tutorial', fields ['sha_draft']
        db.create_index(u'tutorial_tutorial', ['sha_draft'])

        # Adding index on 'Tutorial', fields ['type']
        db.create_index(u'tutorial_tutorial', ['type'])

        # Adding index on 'Chapter', fields ['position_in_part']
        db.create_index(u'tutorial_chapter', ['position_in_part'])

        # Adding index on 'Extract', fields ['position_in_chapter']
        db.create_index(u'tutorial_extract', ['position_in_chapter'])

        # Adding index on 'Part', fields ['position_in_tutorial']
        db.create_index(u'tutorial_part', ['position_in_tutorial'])

        # Adding index on 'Validation', fields ['version']
        db.create_index(u'tutorial_validation', ['version'])

        # Adding index on 'Validation', fields ['date_proposition']
        db.create_index(u'tutorial_validation', ['date_proposition'])


    def backwards(self, orm):
        # Removing index on 'Validation', fields ['date_proposition']
        db.delete_index(u'tutorial_validation', ['date_proposition'])

        # Removing index on 'Validation', fields ['version']
        db.delete_index(u'tutorial_validation', ['version'])

        # Removing index on 'Part', fields ['position_in_tutorial']
        db.delete_index(u'tutorial_part', ['position_in_tutorial'])

        # Removing index on 'Extract', fields ['position_in_chapter']
        db.delete_index(u'tutorial_extract', ['position_in_chapter'])

        # Removing index on 'Chapter', fields ['position_in_part']
        db.delete_index(u'tutorial_chapter', ['position_in_part'])

        # Removing index on 'Tutorial', fields ['type']
        db.delete_index(u'tutorial_tutorial', ['type'])

        # Removing index on 'Tutorial', fields ['sha_draft']
        db.delete_index(u'tutorial_tutorial', ['sha_draft'])

        # Removing index on 'Tutorial', fields ['sha_validation']
        db.delete_index(u'tutorial_tutorial', ['sha_validation'])

        # Removing index on 'Tutorial', fields ['sha_beta']
        db.delete_index(u'tutorial_tutorial', ['sha_beta'])

        # Removing index on 'Tutorial', fields ['sha_public']
        db.delete_index(u'tutorial_tutorial', ['sha_public'])

        # Removing index on 'Tutorial', fields ['pubdate']
        db.delete_index(u'tutorial_tutorial', ['pubdate'])


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
            'medium': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'physical': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'pubdate': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '80'}),
            'thumb': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '80', 'null': 'True', 'blank': 'True'}),
            'update': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        u'tutorial.chapter': {
            'Meta': {'object_name': 'Chapter'},
            'conclusion': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['gallery.Image']", 'null': 'True', 'blank': 'True'}),
            'introduction': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'part': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tutorial.Part']", 'null': 'True', 'blank': 'True'}),
            'position_in_part': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'position_in_tutorial': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '80'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '80', 'blank': 'True'}),
            'tutorial': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tutorial.Tutorial']", 'null': 'True', 'blank': 'True'})
        },
        u'tutorial.extract': {
            'Meta': {'object_name': 'Extract'},
            'chapter': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tutorial.Chapter']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'position_in_chapter': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'text': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '80'})
        },
        u'tutorial.note': {
            'Meta': {'object_name': 'Note', '_ormbases': [u'utils.Comment']},
            u'comment_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['utils.Comment']", 'unique': 'True', 'primary_key': 'True'}),
            'tutorial': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tutorial.Tutorial']"})
        },
        u'tutorial.part': {
            'Meta': {'object_name': 'Part'},
            'conclusion': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'introduction': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'position_in_tutorial': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '80'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'tutorial': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tutorial.Tutorial']"})
        },
        u'tutorial.tutorial': {
            'Meta': {'object_name': 'Tutorial'},
            'authors': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.User']", 'db_index': 'True', 'symmetrical': 'False'}),
            'conclusion': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'create_at': ('django.db.models.fields.DateTimeField', [], {}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'gallery': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['gallery.Gallery']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['gallery.Image']", 'null': 'True', 'blank': 'True'}),
            'images': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'introduction': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'is_locked': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_note': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'last_note'", 'null': 'True', 'to': u"orm['tutorial.Note']"}),
            'licence': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['utils.Licence']", 'null': 'True', 'blank': 'True'}),
            'pubdate': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'sha_beta': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '80', 'null': 'True', 'blank': 'True'}),
            'sha_draft': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '80', 'null': 'True', 'blank': 'True'}),
            'sha_public': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '80', 'null': 'True', 'blank': 'True'}),
            'sha_validation': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '80', 'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '80'}),
            'subcategory': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['utils.SubCategory']", 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '10', 'db_index': 'True'}),
            'update': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        u'tutorial.tutorialread': {
            'Meta': {'object_name': 'TutorialRead'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'note': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tutorial.Note']"}),
            'tutorial': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tutorial.Tutorial']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tuto_notes_read'", 'to': u"orm['auth.User']"})
        },
        u'tutorial.validation': {
            'Meta': {'object_name': 'Validation'},
            'comment_authors': ('django.db.models.fields.TextField', [], {}),
            'comment_validator': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'date_proposition': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'date_reserve': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'date_validation': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'PENDING'", 'max_length': '10'}),
            'tutorial': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tutorial.Tutorial']", 'null': 'True', 'blank': 'True'}),
            'validator': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'author_validations'", 'null': 'True', 'to': u"orm['auth.User']"}),
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

    complete_apps = ['tutorial']