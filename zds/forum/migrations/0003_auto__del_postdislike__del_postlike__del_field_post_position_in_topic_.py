# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'PostDislike'
        db.delete_table(u'forum_postdislike')

        # Deleting model 'PostLike'
        db.delete_table(u'forum_postlike')

        # Deleting field 'Post.position_in_topic'
        db.delete_column(u'forum_post', 'position_in_topic')

        # Deleting field 'Post.is_visible'
        db.delete_column(u'forum_post', 'is_visible')

        # Deleting field 'Post.like'
        db.delete_column(u'forum_post', 'like')

        # Deleting field 'Post.pubdate'
        db.delete_column(u'forum_post', 'pubdate')

        # Deleting field 'Post.author'
        db.delete_column(u'forum_post', 'author_id')

        # Deleting field 'Post.text'
        db.delete_column(u'forum_post', 'text')

        # Deleting field 'Post.update'
        db.delete_column(u'forum_post', 'update')

        # Deleting field 'Post.text_hidden'
        db.delete_column(u'forum_post', 'text_hidden')

        # Deleting field 'Post.editor'
        db.delete_column(u'forum_post', 'editor_id')

        # Deleting field 'Post.text_html'
        db.delete_column(u'forum_post', 'text_html')

        # Deleting field 'Post.dislike'
        db.delete_column(u'forum_post', 'dislike')

        # Deleting field 'Post.ip_address'
        db.delete_column(u'forum_post', 'ip_address')

        # Deleting field 'Post.id'
        db.delete_column(u'forum_post', u'id')

        # Adding field 'Post.comment_ptr'
        db.add_column(u'forum_post', u'comment_ptr',
                      self.gf('django.db.models.fields.related.OneToOneField')(default=1, to=orm['utils.Comment'], unique=True, primary_key=True),
                      keep_default=False)

        # Removing M2M table for field alerts on 'Post'
        db.delete_table(db.shorten_name(u'forum_post_alerts'))


    def backwards(self, orm):
        # Adding model 'PostDislike'
        db.create_table(u'forum_postdislike', (
            ('posts', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['forum.Post'])),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='post_disliked', to=orm['auth.User'])),
        ))
        db.send_create_signal(u'forum', ['PostDislike'])

        # Adding model 'PostLike'
        db.create_table(u'forum_postlike', (
            ('posts', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['forum.Post'])),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='post_liked', to=orm['auth.User'])),
        ))
        db.send_create_signal(u'forum', ['PostLike'])


        # User chose to not deal with backwards NULL issues for 'Post.position_in_topic'
        raise RuntimeError("Cannot reverse this migration. 'Post.position_in_topic' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration        # Adding field 'Post.position_in_topic'
        db.add_column(u'forum_post', 'position_in_topic',
                      self.gf('django.db.models.fields.IntegerField')(),
                      keep_default=False)

        # Adding field 'Post.is_visible'
        db.add_column(u'forum_post', 'is_visible',
                      self.gf('django.db.models.fields.BooleanField')(default=True),
                      keep_default=False)

        # Adding field 'Post.like'
        db.add_column(u'forum_post', 'like',
                      self.gf('django.db.models.fields.IntegerField')(default=0),
                      keep_default=False)


        # User chose to not deal with backwards NULL issues for 'Post.pubdate'
        raise RuntimeError("Cannot reverse this migration. 'Post.pubdate' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration        # Adding field 'Post.pubdate'
        db.add_column(u'forum_post', 'pubdate',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True),
                      keep_default=False)


        # User chose to not deal with backwards NULL issues for 'Post.author'
        raise RuntimeError("Cannot reverse this migration. 'Post.author' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration        # Adding field 'Post.author'
        db.add_column(u'forum_post', 'author',
                      self.gf('django.db.models.fields.related.ForeignKey')(related_name='posts', to=orm['auth.User']),
                      keep_default=False)


        # User chose to not deal with backwards NULL issues for 'Post.text'
        raise RuntimeError("Cannot reverse this migration. 'Post.text' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration        # Adding field 'Post.text'
        db.add_column(u'forum_post', 'text',
                      self.gf('django.db.models.fields.TextField')(),
                      keep_default=False)

        # Adding field 'Post.update'
        db.add_column(u'forum_post', 'update',
                      self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'Post.text_hidden'
        db.add_column(u'forum_post', 'text_hidden',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=80),
                      keep_default=False)

        # Adding field 'Post.editor'
        db.add_column(u'forum_post', 'editor',
                      self.gf('django.db.models.fields.related.ForeignKey')(related_name='posts-editor', null=True, to=orm['auth.User'], blank=True),
                      keep_default=False)


        # User chose to not deal with backwards NULL issues for 'Post.text_html'
        raise RuntimeError("Cannot reverse this migration. 'Post.text_html' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration        # Adding field 'Post.text_html'
        db.add_column(u'forum_post', 'text_html',
                      self.gf('django.db.models.fields.TextField')(),
                      keep_default=False)

        # Adding field 'Post.dislike'
        db.add_column(u'forum_post', 'dislike',
                      self.gf('django.db.models.fields.IntegerField')(default=0),
                      keep_default=False)


        # User chose to not deal with backwards NULL issues for 'Post.ip_address'
        raise RuntimeError("Cannot reverse this migration. 'Post.ip_address' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration        # Adding field 'Post.ip_address'
        db.add_column(u'forum_post', 'ip_address',
                      self.gf('django.db.models.fields.CharField')(max_length=15),
                      keep_default=False)


        # User chose to not deal with backwards NULL issues for 'Post.id'
        raise RuntimeError("Cannot reverse this migration. 'Post.id' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration        # Adding field 'Post.id'
        db.add_column(u'forum_post', u'id',
                      self.gf('django.db.models.fields.AutoField')(primary_key=True),
                      keep_default=False)

        # Deleting field 'Post.comment_ptr'
        db.delete_column(u'forum_post', u'comment_ptr_id')

        # Adding M2M table for field alerts on 'Post'
        m2m_table_name = db.shorten_name(u'forum_post_alerts')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('post', models.ForeignKey(orm[u'forum.post'], null=False)),
            ('alert', models.ForeignKey(orm[u'utils.alert'], null=False))
        ))
        db.create_unique(m2m_table_name, ['post_id', 'alert_id'])


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
        u'forum.category': {
            'Meta': {'object_name': 'Category'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'position': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '80'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '80'})
        },
        u'forum.forum': {
            'Meta': {'object_name': 'Forum'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['forum.Category']"}),
            'group': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['auth.Group']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'position_in_category': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '80'}),
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
            'subtitle': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '60'})
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
        u'utils.alert': {
            'Meta': {'object_name': 'Alert'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'alerts'", 'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pubdate': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {})
        },
        u'utils.comment': {
            'Meta': {'object_name': 'Comment'},
            'alerts': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['utils.Alert']", 'null': 'True', 'blank': 'True'}),
            'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'posts'", 'to': u"orm['auth.User']"}),
            'dislike': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'editor': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'posts-editor'", 'null': 'True', 'to': u"orm['auth.User']"}),
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
        }
    }

    complete_apps = ['forum']