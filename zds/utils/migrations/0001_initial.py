# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Alert'
        db.create_table(u'utils_alert', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(related_name='alerts', to=orm['auth.User'])),
            ('text', self.gf('django.db.models.fields.TextField')()),
            ('pubdate', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'utils', ['Alert'])

        # Adding model 'Category'
        db.create_table(u'utils_category', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=80)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=80)),
        ))
        db.send_create_signal(u'utils', ['Category'])

        # Adding model 'SubCategory'
        db.create_table(u'utils_subcategory', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=80)),
            ('subtitle', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('image', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True, blank=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=80)),
        ))
        db.send_create_signal(u'utils', ['SubCategory'])

        # Adding model 'CategorySubCategory'
        db.create_table(u'utils_categorysubcategory', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['utils.Category'])),
            ('subcategory', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['utils.SubCategory'])),
            ('is_main', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal(u'utils', ['CategorySubCategory'])

        # Adding model 'Licence'
        db.create_table(u'utils_licence', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=80)),
            ('description', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'utils', ['Licence'])

        # Adding model 'Comment'
        db.create_table(u'utils_comment', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(related_name='comments', to=orm['auth.User'])),
            ('editor', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='comments-editor', null=True, to=orm['auth.User'])),
            ('ip_address', self.gf('django.db.models.fields.CharField')(max_length=15)),
            ('position', self.gf('django.db.models.fields.IntegerField')()),
            ('text', self.gf('django.db.models.fields.TextField')()),
            ('text_html', self.gf('django.db.models.fields.TextField')()),
            ('like', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('dislike', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('pubdate', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('update', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('is_visible', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('text_hidden', self.gf('django.db.models.fields.CharField')(default='', max_length=80)),
        ))
        db.send_create_signal(u'utils', ['Comment'])

        # Adding M2M table for field alerts on 'Comment'
        m2m_table_name = db.shorten_name(u'utils_comment_alerts')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('comment', models.ForeignKey(orm[u'utils.comment'], null=False)),
            ('alert', models.ForeignKey(orm[u'utils.alert'], null=False))
        ))
        db.create_unique(m2m_table_name, ['comment_id', 'alert_id'])

        # Adding model 'CommentLike'
        db.create_table(u'utils_commentlike', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('comments', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['utils.Comment'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='post_liked', to=orm['auth.User'])),
        ))
        db.send_create_signal(u'utils', ['CommentLike'])

        # Adding model 'CommentDislike'
        db.create_table(u'utils_commentdislike', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('comments', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['utils.Comment'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='post_disliked', to=orm['auth.User'])),
        ))
        db.send_create_signal(u'utils', ['CommentDislike'])


    def backwards(self, orm):
        # Deleting model 'Alert'
        db.delete_table(u'utils_alert')

        # Deleting model 'Category'
        db.delete_table(u'utils_category')

        # Deleting model 'SubCategory'
        db.delete_table(u'utils_subcategory')

        # Deleting model 'CategorySubCategory'
        db.delete_table(u'utils_categorysubcategory')

        # Deleting model 'Licence'
        db.delete_table(u'utils_licence')

        # Deleting model 'Comment'
        db.delete_table(u'utils_comment')

        # Removing M2M table for field alerts on 'Comment'
        db.delete_table(db.shorten_name(u'utils_comment_alerts'))

        # Deleting model 'CommentLike'
        db.delete_table(u'utils_commentlike')

        # Deleting model 'CommentDislike'
        db.delete_table(u'utils_commentdislike')


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
        u'utils.alert': {
            'Meta': {'object_name': 'Alert'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'alerts'", 'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pubdate': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {})
        },
        u'utils.category': {
            'Meta': {'object_name': 'Category'},
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '80'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '80'})
        },
        u'utils.categorysubcategory': {
            'Meta': {'object_name': 'CategorySubCategory'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['utils.Category']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_main': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'subcategory': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['utils.SubCategory']"})
        },
        u'utils.comment': {
            'Meta': {'object_name': 'Comment'},
            'alerts': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['utils.Alert']", 'null': 'True', 'blank': 'True'}),
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
        u'utils.commentdislike': {
            'Meta': {'object_name': 'CommentDislike'},
            'comments': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['utils.Comment']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'post_disliked'", 'to': u"orm['auth.User']"})
        },
        u'utils.commentlike': {
            'Meta': {'object_name': 'CommentLike'},
            'comments': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['utils.Comment']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'post_liked'", 'to': u"orm['auth.User']"})
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

    complete_apps = ['utils']