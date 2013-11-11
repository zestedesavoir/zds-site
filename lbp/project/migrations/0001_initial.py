# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'BPlan'
        db.create_table(u'project_bplan', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('short_description', self.gf('django.db.models.fields.TextField')()),
            ('long_description', self.gf('django.db.models.fields.TextField')()),
            ('roadmap', self.gf('django.db.models.fields.TextField')()),
            ('market_study', self.gf('django.db.models.fields.TextField')()),
            ('product', self.gf('django.db.models.fields.TextField')()),
            ('pricing', self.gf('django.db.models.fields.TextField')()),
            ('promote', self.gf('django.db.models.fields.TextField')()),
            ('place', self.gf('django.db.models.fields.TextField')()),
            ('strategy', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'project', ['BPlan'])

        # Adding model 'Project'
        db.create_table(u'project_project', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=80)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('bplan', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['project.BPlan'], null=True, blank=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=80)),
            ('image', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['gallery.Image'], null=True, blank=True)),
            ('gallery', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['gallery.Gallery'], null=True, blank=True)),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(related_name='projets', to=orm['auth.User'])),
            ('state', self.gf('django.db.models.fields.CharField')(default='PENDING', max_length=15)),
            ('last_version', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['project.Project'], null=True, blank=True)),
            ('date', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['utils.DateManager'])),
        ))
        db.send_create_signal(u'project', ['Project'])

        # Adding M2M table for field categories on 'Project'
        m2m_table_name = db.shorten_name(u'project_project_categories')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('project', models.ForeignKey(orm[u'project.project'], null=False)),
            ('category', models.ForeignKey(orm[u'utils.category'], null=False))
        ))
        db.create_unique(m2m_table_name, ['project_id', 'category_id'])

        # Adding M2M table for field technologies on 'Project'
        m2m_table_name = db.shorten_name(u'project_project_technologies')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('project', models.ForeignKey(orm[u'project.project'], null=False)),
            ('technology', models.ForeignKey(orm[u'project.technology'], null=False))
        ))
        db.create_unique(m2m_table_name, ['project_id', 'technology_id'])

        # Adding M2M table for field plateforms on 'Project'
        m2m_table_name = db.shorten_name(u'project_project_plateforms')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('project', models.ForeignKey(orm[u'project.project'], null=False)),
            ('plateform', models.ForeignKey(orm[u'project.plateform'], null=False))
        ))
        db.create_unique(m2m_table_name, ['project_id', 'plateform_id'])

        # Adding model 'ProjectFollowed'
        db.create_table(u'project_projectfollowed', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['project.Project'])),
        ))
        db.send_create_signal(u'project', ['ProjectFollowed'])

        # Adding model 'ProjectRead'
        db.create_table(u'project_projectread', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['project.Project'])),
        ))
        db.send_create_signal(u'project', ['ProjectRead'])

        # Adding model 'Fonction'
        db.create_table(u'project_fonction', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=80)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('create_at', self.gf('django.db.models.fields.DateTimeField')()),
            ('pubdate', self.gf('django.db.models.fields.DateTimeField')()),
            ('update', self.gf('django.db.models.fields.DateTimeField')()),
            ('public', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'project', ['Fonction'])

        # Adding model 'Technology'
        db.create_table(u'project_technology', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=80)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('public', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'project', ['Technology'])

        # Adding model 'Plateform'
        db.create_table(u'project_plateform', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=80)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('public', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'project', ['Plateform'])

        # Adding model 'Criteria'
        db.create_table(u'project_criteria', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=80)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('public', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('score_max', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal(u'project', ['Criteria'])

        # Adding model 'Evaluation'
        db.create_table(u'project_evaluation', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['project.Project'])),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('criteria', self.gf('django.db.models.fields.related.ForeignKey')(related_name='evaluations', to=orm['project.Criteria'])),
            ('note', self.gf('django.db.models.fields.related.ForeignKey')(related_name='evaluations+', blank=True, to=orm['project.Note'])),
            ('comment', self.gf('django.db.models.fields.TextField')()),
            ('public', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'project', ['Evaluation'])

        # Adding model 'Note'
        db.create_table(u'project_note', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=5)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('score', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal(u'project', ['Note'])

        # Adding model 'Participation'
        db.create_table(u'project_participation', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='participations', to=orm['auth.User'])),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(related_name='participations', to=orm['project.Project'])),
            ('fonction', self.gf('django.db.models.fields.related.ForeignKey')(related_name='participations', to=orm['project.Fonction'])),
        ))
        db.send_create_signal(u'project', ['Participation'])

        # Adding model 'CompetenceFonctionnelle'
        db.create_table(u'project_competencefonctionnelle', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='fdcompetences', to=orm['auth.User'])),
            ('other', self.gf('django.db.models.fields.related.ForeignKey')(related_name='fecompetences', to=orm['auth.User'])),
            ('fonction', self.gf('django.db.models.fields.related.ForeignKey')(related_name='fcompetences', to=orm['project.Fonction'])),
        ))
        db.send_create_signal(u'project', ['CompetenceFonctionnelle'])

        # Adding M2M table for field notes on 'CompetenceFonctionnelle'
        m2m_table_name = db.shorten_name(u'project_competencefonctionnelle_notes')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('competencefonctionnelle', models.ForeignKey(orm[u'project.competencefonctionnelle'], null=False)),
            ('note', models.ForeignKey(orm[u'project.note'], null=False))
        ))
        db.create_unique(m2m_table_name, ['competencefonctionnelle_id', 'note_id'])

        # Adding model 'CompetenceTechno'
        db.create_table(u'project_competencetechno', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='tdcompetences', to=orm['auth.User'])),
            ('other', self.gf('django.db.models.fields.related.ForeignKey')(related_name='tecompetences', to=orm['auth.User'])),
            ('technology', self.gf('django.db.models.fields.related.ForeignKey')(related_name='tcompetences', to=orm['project.Technology'])),
        ))
        db.send_create_signal(u'project', ['CompetenceTechno'])

        # Adding M2M table for field notes on 'CompetenceTechno'
        m2m_table_name = db.shorten_name(u'project_competencetechno_notes')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('competencetechno', models.ForeignKey(orm[u'project.competencetechno'], null=False)),
            ('note', models.ForeignKey(orm[u'project.note'], null=False))
        ))
        db.create_unique(m2m_table_name, ['competencetechno_id', 'note_id'])

        # Adding model 'CompetencePlateforme'
        db.create_table(u'project_competenceplateforme', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='pdcompetences', to=orm['auth.User'])),
            ('other', self.gf('django.db.models.fields.related.ForeignKey')(related_name='pecompetences', to=orm['auth.User'])),
            ('plateform', self.gf('django.db.models.fields.related.ForeignKey')(related_name='pcompetences', to=orm['project.Plateform'])),
        ))
        db.send_create_signal(u'project', ['CompetencePlateforme'])

        # Adding M2M table for field notes on 'CompetencePlateforme'
        m2m_table_name = db.shorten_name(u'project_competenceplateforme_notes')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('competenceplateforme', models.ForeignKey(orm[u'project.competenceplateforme'], null=False)),
            ('note', models.ForeignKey(orm[u'project.note'], null=False))
        ))
        db.create_unique(m2m_table_name, ['competenceplateforme_id', 'note_id'])


    def backwards(self, orm):
        # Deleting model 'BPlan'
        db.delete_table(u'project_bplan')

        # Deleting model 'Project'
        db.delete_table(u'project_project')

        # Removing M2M table for field categories on 'Project'
        db.delete_table(db.shorten_name(u'project_project_categories'))

        # Removing M2M table for field technologies on 'Project'
        db.delete_table(db.shorten_name(u'project_project_technologies'))

        # Removing M2M table for field plateforms on 'Project'
        db.delete_table(db.shorten_name(u'project_project_plateforms'))

        # Deleting model 'ProjectFollowed'
        db.delete_table(u'project_projectfollowed')

        # Deleting model 'ProjectRead'
        db.delete_table(u'project_projectread')

        # Deleting model 'Fonction'
        db.delete_table(u'project_fonction')

        # Deleting model 'Technology'
        db.delete_table(u'project_technology')

        # Deleting model 'Plateform'
        db.delete_table(u'project_plateform')

        # Deleting model 'Criteria'
        db.delete_table(u'project_criteria')

        # Deleting model 'Evaluation'
        db.delete_table(u'project_evaluation')

        # Deleting model 'Note'
        db.delete_table(u'project_note')

        # Deleting model 'Participation'
        db.delete_table(u'project_participation')

        # Deleting model 'CompetenceFonctionnelle'
        db.delete_table(u'project_competencefonctionnelle')

        # Removing M2M table for field notes on 'CompetenceFonctionnelle'
        db.delete_table(db.shorten_name(u'project_competencefonctionnelle_notes'))

        # Deleting model 'CompetenceTechno'
        db.delete_table(u'project_competencetechno')

        # Removing M2M table for field notes on 'CompetenceTechno'
        db.delete_table(db.shorten_name(u'project_competencetechno_notes'))

        # Deleting model 'CompetencePlateforme'
        db.delete_table(u'project_competenceplateforme')

        # Removing M2M table for field notes on 'CompetencePlateforme'
        db.delete_table(db.shorten_name(u'project_competenceplateforme_notes'))


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
        u'project.bplan': {
            'Meta': {'object_name': 'BPlan'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'long_description': ('django.db.models.fields.TextField', [], {}),
            'market_study': ('django.db.models.fields.TextField', [], {}),
            'place': ('django.db.models.fields.TextField', [], {}),
            'pricing': ('django.db.models.fields.TextField', [], {}),
            'product': ('django.db.models.fields.TextField', [], {}),
            'promote': ('django.db.models.fields.TextField', [], {}),
            'roadmap': ('django.db.models.fields.TextField', [], {}),
            'short_description': ('django.db.models.fields.TextField', [], {}),
            'strategy': ('django.db.models.fields.TextField', [], {})
        },
        u'project.competencefonctionnelle': {
            'Meta': {'object_name': 'CompetenceFonctionnelle'},
            'fonction': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'fcompetences'", 'to': u"orm['project.Fonction']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notes': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'fcompetences+'", 'blank': 'True', 'to': u"orm['project.Note']"}),
            'other': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'fecompetences'", 'to': u"orm['auth.User']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'fdcompetences'", 'to': u"orm['auth.User']"})
        },
        u'project.competenceplateforme': {
            'Meta': {'object_name': 'CompetencePlateforme'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notes': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'pcompetences+'", 'blank': 'True', 'to': u"orm['project.Note']"}),
            'other': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'pecompetences'", 'to': u"orm['auth.User']"}),
            'plateform': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'pcompetences'", 'to': u"orm['project.Plateform']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'pdcompetences'", 'to': u"orm['auth.User']"})
        },
        u'project.competencetechno': {
            'Meta': {'object_name': 'CompetenceTechno'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notes': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'tcompetences+'", 'blank': 'True', 'to': u"orm['project.Note']"}),
            'other': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tecompetences'", 'to': u"orm['auth.User']"}),
            'technology': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tcompetences'", 'to': u"orm['project.Technology']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tdcompetences'", 'to': u"orm['auth.User']"})
        },
        u'project.criteria': {
            'Meta': {'ordering': "('title',)", 'object_name': 'Criteria'},
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'score_max': ('django.db.models.fields.IntegerField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '80'})
        },
        u'project.evaluation': {
            'Meta': {'object_name': 'Evaluation'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'comment': ('django.db.models.fields.TextField', [], {}),
            'criteria': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'evaluations'", 'to': u"orm['project.Criteria']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'note': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'evaluations+'", 'blank': 'True', 'to': u"orm['project.Note']"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['project.Project']"}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'project.fonction': {
            'Meta': {'ordering': "('title',)", 'object_name': 'Fonction'},
            'create_at': ('django.db.models.fields.DateTimeField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pubdate': ('django.db.models.fields.DateTimeField', [], {}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'update': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'project.note': {
            'Meta': {'ordering': "('score',)", 'object_name': 'Note'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'score': ('django.db.models.fields.IntegerField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        u'project.participation': {
            'Meta': {'object_name': 'Participation'},
            'fonction': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'participations'", 'to': u"orm['project.Fonction']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'participations'", 'to': u"orm['project.Project']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'participations'", 'to': u"orm['auth.User']"})
        },
        u'project.plateform': {
            'Meta': {'ordering': "('title',)", 'object_name': 'Plateform'},
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '80'})
        },
        u'project.project': {
            'Meta': {'ordering': "('date__update',)", 'object_name': 'Project'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'projets'", 'to': u"orm['auth.User']"}),
            'bplan': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['project.BPlan']", 'null': 'True', 'blank': 'True'}),
            'categories': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'projets+'", 'blank': 'True', 'to': u"orm['utils.Category']"}),
            'date': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['utils.DateManager']"}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'gallery': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['gallery.Gallery']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['gallery.Image']", 'null': 'True', 'blank': 'True'}),
            'last_version': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['project.Project']", 'null': 'True', 'blank': 'True'}),
            'plateforms': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'projets+'", 'blank': 'True', 'to': u"orm['project.Plateform']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '80'}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'PENDING'", 'max_length': '15'}),
            'technologies': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'projets+'", 'blank': 'True', 'to': u"orm['project.Technology']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '80'})
        },
        u'project.projectfollowed': {
            'Meta': {'object_name': 'ProjectFollowed'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['project.Project']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'project.projectread': {
            'Meta': {'object_name': 'ProjectRead'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['project.Project']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'project.technology': {
            'Meta': {'ordering': "('title',)", 'object_name': 'Technology'},
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '80'})
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
        }
    }

    complete_apps = ['project']