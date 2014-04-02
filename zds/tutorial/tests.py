# coding: utf-8

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings

from zds.member.factories import *
from zds.settings import SITE_ROOT
from zds.tutorial.factories import *
from zds.utils.models import CommentLike, CommentDislike

import shutil
from .models import *


@override_settings(MEDIA_ROOT=os.path.join(SITE_ROOT, 'media-test'))
@override_settings(REPO_PATH=os.path.join(SITE_ROOT, 'tutoriels-private-test'))
@override_settings(REPO_PATH_PROD=os.path.join(SITE_ROOT, 'tutoriels-public-test'))
@override_settings(REPO_ARTICLE_PATH=os.path.join(SITE_ROOT, 'articles-data-test'))

class BigTutorialTests(TestCase):
    
    def setUp(self):
        
        settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
        
        self.bigtuto = BigTutorialFactory()
        
        self.part1 = PartFactory(tutorial=self.bigtuto, position_in_tutorial=1)
        self.part2 = PartFactory(tutorial=self.bigtuto, position_in_tutorial=2)
        self.part3 = PartFactory(tutorial=self.bigtuto, position_in_tutorial=3)
        
        self.chapter1_1 = ChapterFactory(part=self.part1, position_in_part=1)
        self.chapter1_2 = ChapterFactory(part=self.part1, position_in_part=2)
        self.chapter1_3 = ChapterFactory(part=self.part1, position_in_part=3)
        
        self.chapter2_1 = ChapterFactory(part=self.part2, position_in_part=1)
        self.chapter2_2 = ChapterFactory(part=self.part2, position_in_part=2)
        
        self.user = UserFactory()
        self.staff = StaffFactory()
        
        login_check = self.client.login(username=self.staff.username, password='hostel77')
        self.assertEqual(login_check, True)
        
        #ask public tutorial
        pub = self.client.post(
                        reverse('zds.tutorial.views.ask_validation'), 
                        {
                          'tutorial' : self.bigtuto.pk,
                          'text': u'Ce tuto est excellent',
                          'version': self.bigtuto.sha_draft
                        },
                        follow=False)
        self.assertEqual(pub.status_code, 302)
        
        #publish tutorial
        pub = self.client.post(
                        reverse('zds.tutorial.views.valid_tutorial'), 
                        {
                          'tutorial' : self.bigtuto.pk,
                          'text': u'Ce tuto est excellent'
                        },
                        follow=False)
        self.assertEqual(pub.status_code, 302)
    
    def test_add_note(self):
        '''
        To test add note for tutorial
        '''
        user1 = UserFactory()
        self.client.login(username=user1.username, password='hostel77')
        
        #add note
        result = self.client.post(
                        reverse('zds.tutorial.views.answer')+'?tutorial={0}'.format(self.bigtuto.pk), 
                        {
                          'last_note' : '0',
                          'text': u'Histoire de blablater dans les comms du tuto'
                        },
                        follow=False)
        self.assertEqual(result.status_code, 302)
        
        #check notes's number
        self.assertEqual(Note.objects.all().count(), 1)

        #check values
        tuto = Tutorial.objects.get(pk=self.bigtuto.pk)
        self.assertEqual(Note.objects.get(pk=1).tutorial, tuto)
        self.assertEqual(Note.objects.get(pk=1).author.pk, user1.pk)
        self.assertEqual(Note.objects.get(pk=1).position, 1)
        self.assertEqual(Note.objects.get(pk=1).pk, tuto.last_note.pk)
        self.assertEqual(Note.objects.get(pk=1).text, u'Histoire de blablater dans les comms du tuto')
        
        #test antispam return 403
        result = self.client.post(
                        reverse('zds.tutorial.views.answer')+'?tutorial={0}'.format(self.bigtuto.pk), 
                        {
                          'last_note' : tuto.last_note.pk,
                          'text': u'Histoire de tester l\'antispam'
                        },
                        follow=False)
        self.assertEqual(result.status_code, 403)
        
        note1 = NoteFactory(tutorial=self.bigtuto, position=2, author=self.staff)
        
        #test more note
        result = self.client.post(
                        reverse('zds.tutorial.views.answer')+'?tutorial={0}'.format(self.bigtuto.pk), 
                        {
                          'last_note' : self.bigtuto.last_note.pk,
                          'text': u'Histoire de tester l\'antispam'
                        },
                        follow=False)
        self.assertEqual(result.status_code, 302)
        
    
    def test_edit_note(self):
        '''
        To test all aspects of the edition of note
        '''
        user1 = UserFactory()
        self.client.login(username=user1.username, password='hostel77')
        
        note1 = NoteFactory(tutorial=self.bigtuto, position=1, author=self.user)
        note2 = NoteFactory(tutorial=self.bigtuto, position=2, author=user1)

        #normal edit
        result = self.client.post(
                        reverse('zds.tutorial.views.edit_note')+'?message={0}'.format(note2.pk), 
                        {
                          'text': u'Autre texte'
                        },
                        follow=False)
        self.assertEqual(result.status_code, 302)
         
        #check note's number
        self.assertEqual(Note.objects.all().count(), 2)
 
        #check note
        self.assertEqual(Note.objects.get(pk=note1.pk).tutorial, self.bigtuto)
        self.assertEqual(Note.objects.get(pk=note2.pk).tutorial, self.bigtuto)
        self.assertEqual(Note.objects.get(pk=note2.pk).text, u'Autre texte')
        self.assertEqual(Note.objects.get(pk=note2.pk).editor, user1)
        
        #simple member want edit other note
        result = self.client.post(
                        reverse('zds.tutorial.views.edit_note')+'?message={0}'.format(note1.pk), 
                        {
                          'text': u'Autre texte'
                        },
                        follow=False)
        self.assertEqual(result.status_code, 403)
        self.assertNotEqual(Note.objects.get(pk=note1.pk).editor, user1)
        
        #staff want edit other note
        self.client.login(username=self.staff.username, password='hostel77')
        result = self.client.post(
                        reverse('zds.tutorial.views.edit_note')+'?message={0}'.format(note1.pk), 
                        {
                          'text': u'Autre texte'
                        },
                        follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Note.objects.get(pk=note1.pk).editor, self.staff)
    
    def test_quote_note(self):
        '''
        check quote of note
        '''
        user1 = UserFactory()
        self.client.login(username=user1.username, password='hostel77')
        
        note1 = NoteFactory(tutorial=self.bigtuto, position=1, author=self.user)
        note2 = NoteFactory(tutorial=self.bigtuto, position=2, author=user1)
        note3 = NoteFactory(tutorial=self.bigtuto, position=3, author=self.user)
        
        #normal quote => true
        result = self.client.get(
                        reverse('zds.tutorial.views.answer')+'?tutorial={0}&cite={1}'.format(self.bigtuto.pk, note3.pk),
                        follow=False)
        self.assertEqual(result.status_code, 200)
        
        #quote on anstispamm => false
        note4 = NoteFactory(tutorial=self.bigtuto, position=4, author=user1)
        result = self.client.get(
                        reverse('zds.tutorial.views.answer')+'?tutorial={0}&cite={1}'.format(self.bigtuto.pk, note3.pk),
                        follow=False)
        self.assertEqual(result.status_code, 403)
    
    def test_like_note(self):
        '''
        check like a note for tuto
        '''
        user1 = UserFactory()
        self.client.login(username=user1.username, password='hostel77')
        
        note1 = NoteFactory(tutorial=self.bigtuto, position=1, author=self.user)
        note2 = NoteFactory(tutorial=self.bigtuto, position=2, author=user1)
        note3 = NoteFactory(tutorial=self.bigtuto, position=3, author=self.user)
        
        #normal like
        result = self.client.get(
                        reverse('zds.tutorial.views.like_note')+'?message={0}'.format(note3.pk),
                        follow=True)
        self.assertEqual(result.status_code, 200)
        
        self.assertEqual(Note.objects.get(pk=note1.pk).like, 0)
        self.assertEqual(Note.objects.get(pk=note2.pk).like, 0)
        self.assertEqual(Note.objects.get(pk=note3.pk).like, 1)
        
        #like yourself
        result = self.client.get(
                        reverse('zds.tutorial.views.like_note')+'?message={0}'.format(note2.pk),
                        follow=True)
        self.assertEqual(result.status_code, 200)
        
        self.assertEqual(Note.objects.get(pk=note1.pk).like, 0)
        self.assertEqual(Note.objects.get(pk=note2.pk).like, 0)
        self.assertEqual(Note.objects.get(pk=note3.pk).like, 1)
        
        #re-like a post
        result = self.client.get(
                        reverse('zds.tutorial.views.like_note')+'?message={0}'.format(note3.pk),
                        follow=True)
        self.assertEqual(result.status_code, 200)
        
        self.assertEqual(Note.objects.get(pk=note1.pk).like, 0)
        self.assertEqual(Note.objects.get(pk=note2.pk).like, 0)
        self.assertEqual(Note.objects.get(pk=note3.pk).like, 0)
    
    def test_dislike_note(self):
        '''
        check like a note for tuto
        '''
        user1 = UserFactory()
        self.client.login(username=user1.username, password='hostel77')
        
        note1 = NoteFactory(tutorial=self.bigtuto, position=1, author=self.user)
        note2 = NoteFactory(tutorial=self.bigtuto, position=2, author=user1)
        note3 = NoteFactory(tutorial=self.bigtuto, position=3, author=self.user)
        
        #normal like
        result = self.client.get(
                        reverse('zds.tutorial.views.dislike_note')+'?message={0}'.format(note3.pk),
                        follow=True)
        self.assertEqual(result.status_code, 200)
        
        self.assertEqual(Note.objects.get(pk=note1.pk).dislike, 0)
        self.assertEqual(Note.objects.get(pk=note2.pk).dislike, 0)
        self.assertEqual(Note.objects.get(pk=note3.pk).dislike, 1)
        
        #like yourself
        result = self.client.get(
                        reverse('zds.tutorial.views.dislike_note')+'?message={0}'.format(note2.pk),
                        follow=True)
        self.assertEqual(result.status_code, 200)
        
        self.assertEqual(Note.objects.get(pk=note1.pk).dislike, 0)
        self.assertEqual(Note.objects.get(pk=note2.pk).dislike, 0)
        self.assertEqual(Note.objects.get(pk=note3.pk).dislike, 1)
        
        #re-like a post
        result = self.client.get(
                        reverse('zds.tutorial.views.dislike_note')+'?message={0}'.format(note3.pk),
                        follow=True)
        self.assertEqual(result.status_code, 200)
        
        self.assertEqual(Note.objects.get(pk=note1.pk).dislike, 0)
        self.assertEqual(Note.objects.get(pk=note2.pk).dislike, 0)
        self.assertEqual(Note.objects.get(pk=note3.pk).dislike, 0)
    
    def test_import_tuto(self):
        '''
        Test import of big tuto
        '''
        result = self.client.post(
                        reverse('zds.tutorial.views.import_tuto'), 
                        {
                          'file': open(settings.SITE_ROOT + '/fixtures/tuto/temps-reel-avec-irrlicht/temps-reel-avec-irrlicht.tuto', 'r'),
                          'images': open(settings.SITE_ROOT + '/fixtures/tuto/temps-reel-avec-irrlicht/images.zip', 'r')
                        },
                        follow=False)
        self.assertEqual(result.status_code, 302)
        
        self.assertEqual(Tutorial.objects.all().count(), 2)
        
    def tearDown(self):
        if os.path.isdir(settings.REPO_PATH): shutil.rmtree(settings.REPO_PATH)
        if os.path.isdir(settings.REPO_PATH_PROD): shutil.rmtree(settings.REPO_PATH_PROD)
        if os.path.isdir(settings.REPO_ARTICLE_PATH): shutil.rmtree(settings.REPO_ARTICLE_PATH)
        if os.path.isdir(settings.MEDIA_ROOT): shutil.rmtree(settings.MEDIA_ROOT)