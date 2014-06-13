# coding: utf-8

import os
import shutil

from django.conf import settings
from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings

from zds.member.factories import ProfileFactory, StaffProfileFactory
from zds.mp.models import PrivateTopic
from zds.settings import SITE_ROOT
from zds.tutorial.factories import BigTutorialFactory, MiniTutorialFactory, PartFactory, \
    ChapterFactory, NoteFactory
from zds.tutorial.models import Note, Tutorial, Validation, Extract
from zds.utils.models import Alert


@override_settings(MEDIA_ROOT=os.path.join(SITE_ROOT, 'media-test'))
@override_settings(REPO_PATH=os.path.join(SITE_ROOT, 'tutoriels-private-test'))
@override_settings(
    REPO_PATH_PROD=os.path.join(
        SITE_ROOT,
        'tutoriels-public-test'))
@override_settings(
    REPO_ARTICLE_PATH=os.path.join(
        SITE_ROOT,
        'articles-data-test'))
class BigTutorialTests(TestCase):

    def setUp(self):

        settings.EMAIL_BACKEND = \
            'django.core.mail.backends.locmem.EmailBackend'
        self.mas = ProfileFactory().user
        settings.BOT_ACCOUNT = self.mas.username

        self.user_author = ProfileFactory().user
        self.user = ProfileFactory().user
        self.staff = StaffProfileFactory().user

        self.bigtuto = BigTutorialFactory()
        self.bigtuto.authors.add(self.user_author)
        self.bigtuto.save()

        self.part1 = PartFactory(tutorial=self.bigtuto, position_in_tutorial=1)
        self.part2 = PartFactory(tutorial=self.bigtuto, position_in_tutorial=2)
        self.part3 = PartFactory(tutorial=self.bigtuto, position_in_tutorial=3)

        self.chapter1_1 = ChapterFactory(
            part=self.part1,
            position_in_part=1,
            position_in_tutorial=1)
        self.chapter1_2 = ChapterFactory(
            part=self.part1,
            position_in_part=2,
            position_in_tutorial=2)
        self.chapter1_3 = ChapterFactory(
            part=self.part1,
            position_in_part=3,
            position_in_tutorial=3)

        self.chapter2_1 = ChapterFactory(
            part=self.part2,
            position_in_part=1,
            position_in_tutorial=4)
        self.chapter2_2 = ChapterFactory(
            part=self.part2,
            position_in_part=2,
            position_in_tutorial=5)

        self.user = ProfileFactory().user
        self.staff = StaffProfileFactory().user

        login_check = self.client.login(
            username=self.staff.username,
            password='hostel77')
        self.assertEqual(login_check, True)

        # ask public tutorial
        pub = self.client.post(
            reverse('zds.tutorial.views.ask_validation'),
            {
                'tutorial': self.bigtuto.pk,
                'text': u'Ce tuto est excellent',
                'version': self.bigtuto.sha_draft
            },
            follow=False)
        self.assertEqual(pub.status_code, 302)

        # reserve tutorial
        validation = Validation.objects.get(
            tutorial__pk=self.bigtuto.pk)
        pub = self.client.get(
            reverse('zds.tutorial.views.reservation', args=[validation.pk]),
            follow=False)
        self.assertEqual(pub.status_code, 302)

        # publish tutorial
        pub = self.client.post(
            reverse('zds.tutorial.views.valid_tutorial'),
            {
                'tutorial': self.bigtuto.pk,
                'text': u'Ce tuto est excellent',
                'is_major': True
            },
            follow=False)
        self.assertEqual(pub.status_code, 302)
        self.assertEquals(len(mail.outbox), 1)

        mail.outbox = []

    def test_add_note(self):
        """To test add note for tutorial."""
        user1 = ProfileFactory().user
        self.client.login(username=user1.username, password='hostel77')

        # add note
        result = self.client.post(
            reverse('zds.tutorial.views.answer') +
            '?tutorial={0}'.format(
                self.bigtuto.pk),
            {
                'last_note': '0',
                'text': u'Histoire de blablater dans les comms du tuto'},
            follow=False)
        self.assertEqual(result.status_code, 302)

        # check notes's number
        self.assertEqual(Note.objects.all().count(), 1)

        # check values
        tuto = Tutorial.objects.get(pk=self.bigtuto.pk)
        self.assertEqual(Note.objects.get(pk=1).tutorial, tuto)
        self.assertEqual(Note.objects.get(pk=1).author.pk, user1.pk)
        self.assertEqual(Note.objects.get(pk=1).position, 1)
        self.assertEqual(Note.objects.get(pk=1).pk, tuto.last_note.pk)
        self.assertEqual(
            Note.objects.get(
                pk=1).text,
            u'Histoire de blablater dans les comms du tuto')

        # test antispam return 403
        result = self.client.post(
            reverse('zds.tutorial.views.answer') +
            '?tutorial={0}'.format(
                self.bigtuto.pk),
            {
                'last_note': tuto.last_note.pk,
                'text': u'Histoire de tester l\'antispam'},
            follow=False)
        self.assertEqual(result.status_code, 403)

        NoteFactory(
            tutorial=self.bigtuto,
            position=2,
            author=self.staff)

        # test more note
        result = self.client.post(
            reverse('zds.tutorial.views.answer') +
            '?tutorial={0}'.format(
                self.bigtuto.pk),
            {
                'last_note': self.bigtuto.last_note.pk,
                'text': u'Histoire de tester l\'antispam'},
            follow=False)
        self.assertEqual(result.status_code, 302)

    def test_edit_note(self):
        """To test all aspects of the edition of note."""
        user1 = ProfileFactory().user
        self.client.login(username=user1.username, password='hostel77')

        note1 = NoteFactory(
            tutorial=self.bigtuto,
            position=1,
            author=self.user)
        note2 = NoteFactory(tutorial=self.bigtuto, position=2, author=user1)

        # normal edit
        result = self.client.post(
            reverse('zds.tutorial.views.edit_note') +
            '?message={0}'.format(
                note2.pk),
            {
                'text': u'Autre texte'},
            follow=False)
        self.assertEqual(result.status_code, 302)

        # check note's number
        self.assertEqual(Note.objects.all().count(), 2)

        # check note
        self.assertEqual(Note.objects.get(pk=note1.pk).tutorial, self.bigtuto)
        self.assertEqual(Note.objects.get(pk=note2.pk).tutorial, self.bigtuto)
        self.assertEqual(Note.objects.get(pk=note2.pk).text, u'Autre texte')
        self.assertEqual(Note.objects.get(pk=note2.pk).editor, user1)

        # simple member want edit other note
        result = self.client.post(
            reverse('zds.tutorial.views.edit_note') +
            '?message={0}'.format(
                note1.pk),
            {
                'text': u'Autre texte'},
            follow=False)
        self.assertEqual(result.status_code, 403)
        self.assertNotEqual(Note.objects.get(pk=note1.pk).editor, user1)

        # staff want edit other note
        self.client.login(username=self.staff.username, password='hostel77')
        result = self.client.post(
            reverse('zds.tutorial.views.edit_note') +
            '?message={0}'.format(
                note1.pk),
            {
                'text': u'Autre texte'},
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Note.objects.get(pk=note1.pk).editor, self.staff)

    def test_quote_note(self):
        """check quote of note."""
        user1 = ProfileFactory().user
        self.client.login(username=user1.username, password='hostel77')

        NoteFactory(
            tutorial=self.bigtuto,
            position=1,
            author=self.user)
        NoteFactory(tutorial=self.bigtuto, position=2, author=user1)
        note3 = NoteFactory(
            tutorial=self.bigtuto,
            position=3,
            author=self.user)

        # normal quote => true
        result = self.client.get(
            reverse('zds.tutorial.views.answer') +
            '?tutorial={0}&cite={1}'.format(
                self.bigtuto.pk,
                note3.pk),
            follow=False)
        self.assertEqual(result.status_code, 200)

        # quote on anstispamm => false
        NoteFactory(tutorial=self.bigtuto, position=4, author=user1)
        result = self.client.get(
            reverse('zds.tutorial.views.answer') +
            '?tutorial={0}&cite={1}'.format(
                self.bigtuto.pk,
                note3.pk),
            follow=False)
        self.assertEqual(result.status_code, 403)

    def test_like_note(self):
        """check like a note for tuto."""
        user1 = ProfileFactory().user
        self.client.login(username=user1.username, password='hostel77')

        note1 = NoteFactory(
            tutorial=self.bigtuto,
            position=1,
            author=self.user)
        note2 = NoteFactory(tutorial=self.bigtuto, position=2, author=user1)
        note3 = NoteFactory(
            tutorial=self.bigtuto,
            position=3,
            author=self.user)

        # normal like
        result = self.client.get(
            reverse('zds.tutorial.views.like_note') +
            '?message={0}'.format(
                note3.pk),
            follow=True)
        self.assertEqual(result.status_code, 200)

        self.assertEqual(Note.objects.get(pk=note1.pk).like, 0)
        self.assertEqual(Note.objects.get(pk=note2.pk).like, 0)
        self.assertEqual(Note.objects.get(pk=note3.pk).like, 1)

        # like yourself
        result = self.client.get(
            reverse('zds.tutorial.views.like_note') +
            '?message={0}'.format(
                note2.pk),
            follow=True)
        self.assertEqual(result.status_code, 200)

        self.assertEqual(Note.objects.get(pk=note1.pk).like, 0)
        self.assertEqual(Note.objects.get(pk=note2.pk).like, 0)
        self.assertEqual(Note.objects.get(pk=note3.pk).like, 1)

        # re-like a post
        result = self.client.get(
            reverse('zds.tutorial.views.like_note') +
            '?message={0}'.format(
                note3.pk),
            follow=True)
        self.assertEqual(result.status_code, 200)

        self.assertEqual(Note.objects.get(pk=note1.pk).like, 0)
        self.assertEqual(Note.objects.get(pk=note2.pk).like, 0)
        self.assertEqual(Note.objects.get(pk=note3.pk).like, 0)

    def test_dislike_note(self):
        """check like a note for tuto."""
        user1 = ProfileFactory().user
        self.client.login(username=user1.username, password='hostel77')

        note1 = NoteFactory(
            tutorial=self.bigtuto,
            position=1,
            author=self.user)
        note2 = NoteFactory(tutorial=self.bigtuto, position=2, author=user1)
        note3 = NoteFactory(
            tutorial=self.bigtuto,
            position=3,
            author=self.user)

        # normal like
        result = self.client.get(
            reverse('zds.tutorial.views.dislike_note') +
            '?message={0}'.format(
                note3.pk),
            follow=True)
        self.assertEqual(result.status_code, 200)

        self.assertEqual(Note.objects.get(pk=note1.pk).dislike, 0)
        self.assertEqual(Note.objects.get(pk=note2.pk).dislike, 0)
        self.assertEqual(Note.objects.get(pk=note3.pk).dislike, 1)

        # like yourself
        result = self.client.get(
            reverse('zds.tutorial.views.dislike_note') +
            '?message={0}'.format(
                note2.pk),
            follow=True)
        self.assertEqual(result.status_code, 200)

        self.assertEqual(Note.objects.get(pk=note1.pk).dislike, 0)
        self.assertEqual(Note.objects.get(pk=note2.pk).dislike, 0)
        self.assertEqual(Note.objects.get(pk=note3.pk).dislike, 1)

        # re-like a post
        result = self.client.get(
            reverse('zds.tutorial.views.dislike_note') +
            '?message={0}'.format(
                note3.pk),
            follow=True)
        self.assertEqual(result.status_code, 200)

        self.assertEqual(Note.objects.get(pk=note1.pk).dislike, 0)
        self.assertEqual(Note.objects.get(pk=note2.pk).dislike, 0)
        self.assertEqual(Note.objects.get(pk=note3.pk).dislike, 0)

    def test_import_tuto(self):
        """Test import of big tuto."""
        result = self.client.post(
            reverse('zds.tutorial.views.import_tuto'),
            {
                'file': open(
                    os.path.join(
                        settings.SITE_ROOT,
                        'fixtures',
                        'tuto',
                        'temps-reel-avec-irrlicht',
                        'temps-reel-avec-irrlicht.tuto'),
                    'r'),
                'images': open(
                    os.path.join(
                        settings.SITE_ROOT,
                        'fixtures',
                        'tuto',
                        'temps-reel-avec-irrlicht',
                        'images.zip'),
                    'r')},
            follow=False)
        self.assertEqual(result.status_code, 302)

        self.assertEqual(Tutorial.objects.all().count(), 2)

    def test_url_for_guest(self):
        """Test simple get request by guest."""

        # logout before
        self.client.logout()

        # guest can read public tutorials
        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_tutorial_online',
                args=[
                    self.bigtuto.pk,
                    self.bigtuto.slug]),
            follow=True)
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_part_online',
                args=[
                    self.bigtuto.pk,
                    self.bigtuto.slug,
                    self.part2.slug]),
            follow=True)
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse('zds.tutorial.views.view_chapter_online',
                    args=[self.bigtuto.pk,
                          self.bigtuto.slug,
                          self.part2.slug,
                          self.chapter2_1.slug]),
            follow=True)
        self.assertEqual(result.status_code, 200)

        # guest can't read offline tutorials
        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_tutorial',
                args=[
                    self.bigtuto.pk,
                    self.bigtuto.slug]),
            follow=False)
        self.assertEqual(result.status_code, 302)

        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_part',
                args=[
                    self.bigtuto.pk,
                    self.bigtuto.slug,
                    self.part2.slug]),
            follow=False)
        self.assertEqual(result.status_code, 302)

        result = self.client.get(
            reverse('zds.tutorial.views.view_chapter',
                    args=[self.bigtuto.pk,
                          self.bigtuto.slug,
                          self.part2.slug,
                          self.chapter2_1.slug]),
            follow=False)
        self.assertEqual(result.status_code, 302)

    def test_url_for_member(self):
        """Test simple get request by simple member."""

        # logout before
        self.client.logout()
        # login with simple member
        self.assertEqual(
            self.client.login(
                username=self.user.username,
                password='hostel77'),
            True)

        # member who isn't author can read public tutorials
        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_tutorial_online',
                args=[
                    self.bigtuto.pk,
                    self.bigtuto.slug]),
            follow=True)
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_part_online',
                args=[
                    self.bigtuto.pk,
                    self.bigtuto.slug,
                    self.part2.slug]),
            follow=True)
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse('zds.tutorial.views.view_chapter_online',
                    args=[self.bigtuto.pk,
                          self.bigtuto.slug,
                          self.part2.slug,
                          self.chapter2_1.slug]),
            follow=True)
        self.assertEqual(result.status_code, 200)

        # member who isn't author  can't read offline tutorials
        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_tutorial',
                args=[
                    self.bigtuto.pk,
                    self.bigtuto.slug]),
            follow=True)
        self.assertEqual(result.status_code, 403)

        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_part',
                args=[
                    self.bigtuto.pk,
                    self.bigtuto.slug,
                    self.part2.slug]),
            follow=True)
        self.assertEqual(result.status_code, 403)

        result = self.client.get(
            reverse('zds.tutorial.views.view_chapter',
                    args=[self.bigtuto.pk,
                          self.bigtuto.slug,
                          self.part2.slug,
                          self.chapter2_1.slug]),
            follow=True)
        self.assertEqual(result.status_code, 403)

    def test_url_for_author(self):
        """Test simple get request by author."""

        # logout before
        self.client.logout()
        # login with simple member
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)

        # member who isn't author can read public tutorials
        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_tutorial_online',
                args=[
                    self.bigtuto.pk,
                    self.bigtuto.slug]),
            follow=True)
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_part_online',
                args=[
                    self.bigtuto.pk,
                    self.bigtuto.slug,
                    self.part2.slug]),
            follow=True)
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse('zds.tutorial.views.view_chapter_online',
                    args=[self.bigtuto.pk,
                          self.bigtuto.slug,
                          self.part2.slug,
                          self.chapter2_1.slug]),
            follow=True)
        self.assertEqual(result.status_code, 200)

        # member who isn't author  can't read offline tutorials
        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_tutorial',
                args=[
                    self.bigtuto.pk,
                    self.bigtuto.slug]),
            follow=True)
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_part',
                args=[
                    self.bigtuto.pk,
                    self.bigtuto.slug,
                    self.part2.slug]),
            follow=True)
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse('zds.tutorial.views.view_chapter',
                    args=[self.bigtuto.pk,
                          self.bigtuto.slug,
                          self.part2.slug,
                          self.chapter2_1.slug]),
            follow=True)
        self.assertEqual(result.status_code, 200)

    def test_url_for_staff(self):
        """Test simple get request by staff."""

        # logout before
        self.client.logout()
        # login with simple member
        self.assertEqual(
            self.client.login(
                username=self.staff.username,
                password='hostel77'),
            True)

        # member who isn't author can read public tutorials
        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_tutorial_online',
                args=[
                    self.bigtuto.pk,
                    self.bigtuto.slug]),
            follow=True)
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_part_online',
                args=[
                    self.bigtuto.pk,
                    self.bigtuto.slug,
                    self.part2.slug]),
            follow=True)
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse('zds.tutorial.views.view_chapter_online',
                    args=[self.bigtuto.pk,
                          self.bigtuto.slug,
                          self.part2.slug,
                          self.chapter2_1.slug]),
            follow=True)
        self.assertEqual(result.status_code, 200)

        # member who isn't author  can't read offline tutorials
        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_tutorial',
                args=[
                    self.bigtuto.pk,
                    self.bigtuto.slug]),
            follow=True)
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_part',
                args=[
                    self.bigtuto.pk,
                    self.bigtuto.slug,
                    self.part2.slug]),
            follow=True)
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse('zds.tutorial.views.view_chapter',
                    args=[self.bigtuto.pk,
                          self.bigtuto.slug,
                          self.part2.slug,
                          self.chapter2_1.slug]),
            follow=True)
        self.assertEqual(result.status_code, 200)

    def test_alert(self):
        user1 = ProfileFactory().user
        note = NoteFactory(tutorial=self.bigtuto, author=user1, position=1)
        login_check = self.client.login(
            username=self.user.username,
            password='hostel77')
        self.assertEqual(login_check, True)
        # signal note
        result = self.client.post(
            reverse('zds.tutorial.views.edit_note') +
            '?message={0}'.format(
                note.pk),
            {
                'signal_text': 'Troll',
                'signal_message': 'Confirmer',
            },
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Alert.objects.all().count(), 1)

        # connect with staff
        login_check = self.client.login(
            username=self.staff.username,
            password='hostel77')
        self.assertEqual(login_check, True)
        # solve alert
        result = self.client.post(
            reverse('zds.tutorial.views.solve_alert'),
            {
                'alert_pk': Alert.objects.first().pk,
                'text': 'Ok',
                'delete_message': 'Resoudre',
            },
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Alert.objects.all().count(), 0)
        self.assertEqual(
            PrivateTopic.objects.filter(
                author=self.user).count(),
            1)
        self.assertEquals(len(mail.outbox), 0)

    def tearDown(self):
        if os.path.isdir(settings.REPO_PATH):
            shutil.rmtree(settings.REPO_PATH)
        if os.path.isdir(settings.REPO_PATH_PROD):
            shutil.rmtree(settings.REPO_PATH_PROD)
        if os.path.isdir(settings.REPO_ARTICLE_PATH):
            shutil.rmtree(settings.REPO_ARTICLE_PATH)
        if os.path.isdir(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)


@override_settings(MEDIA_ROOT=os.path.join(SITE_ROOT, 'media-test'))
@override_settings(REPO_PATH=os.path.join(SITE_ROOT, 'tutoriels-private-test'))
@override_settings(
    REPO_PATH_PROD=os.path.join(
        SITE_ROOT,
        'tutoriels-public-test'))
@override_settings(
    REPO_ARTICLE_PATH=os.path.join(
        SITE_ROOT,
        'articles-data-test'))
class MiniTutorialTests(TestCase):

    def setUp(self):

        settings.EMAIL_BACKEND = \
            'django.core.mail.backends.locmem.EmailBackend'
        self.mas = ProfileFactory().user
        settings.BOT_ACCOUNT = self.mas.username

        self.user_author = ProfileFactory().user
        self.user = ProfileFactory().user
        self.staff = StaffProfileFactory().user

        self.minituto = MiniTutorialFactory()
        self.minituto.authors.add(self.user_author)
        self.minituto.save()

        self.chapter = ChapterFactory(
            tutorial=self.minituto,
            position_in_tutorial=1)

        self.staff = StaffProfileFactory().user

        login_check = self.client.login(
            username=self.staff.username,
            password='hostel77')
        self.assertEqual(login_check, True)

        # ask public tutorial
        pub = self.client.post(
            reverse('zds.tutorial.views.ask_validation'),
            {
                'tutorial': self.minituto.pk,
                'text': u'Ce tuto est excellent',
                'version': self.minituto.sha_draft
            },
            follow=False)
        self.assertEqual(pub.status_code, 302)

        # reserve tutorial
        validation = Validation.objects.get(
            tutorial__pk=self.minituto.pk)
        pub = self.client.get(
            reverse('zds.tutorial.views.reservation', args=[validation.pk]),
            follow=False)
        self.assertEqual(pub.status_code, 302)

        # publish tutorial
        pub = self.client.post(
            reverse('zds.tutorial.views.valid_tutorial'),
            {
                'tutorial': self.minituto.pk,
                'text': u'Ce tuto est excellent',
                'is_major': True
            },
            follow=False)
        self.assertEqual(pub.status_code, 302)
        self.assertEquals(len(mail.outbox), 1)

        mail.outbox = []

    def add_test_extract_named_introduction(self):
        """test the use of an extract named introduction"""
        
        self.client.login(username=self.user_author,
            password='hostel77')
        
        result = self.client.post(
            reverse( 'zds.tutorial.views.add_extract') +
            '?chapitre={0}'.format(
                self.chapter.pk),
            
            {
            'title' : "Introduction",
            'text' : u"Le contenu de l'extrait"
            })
        self.assertEqual(result.status_code, 302)
        tuto = Tutorial.objects.get(pk=self.minituto.pk)
        self.assertEqual(Extract.objects.all().count(),1)
        intro_path = os.path.join(tuto.get_path(),"introduction.md")
        extract_path =  Extract.objects.get(pk=1).get_path()
        self.assertNotEqual(intro_path,extract_path)
        self.assertTrue(os.path.isfile(intro_path))
        self.assertTrue(os.path.isfile(extract_path))

    def add_test_extract_named_conclusion(self):
        """test the use of an extract named introduction"""
        
        self.client.login(username=self.user_author,
            password='hostel77')
        
        result = self.client.post(
            reverse( 'zds.tutorial.views.add_extract') +
            '?chapitre={0}'.format(
                self.chapter.pk),
            
            {
            'title' : "Conclusion",
            'text' : u"Le contenu de l'extrait"
            })
        self.assertEqual(result.status_code, 302)
        tuto = Tutorial.objects.get(pk=self.minituto.pk)
        self.assertEqual(Extract.objects.all().count(),1)
        ccl_path = os.path.join(tuto.get_path(),"conclusion.md")
        extract_path =  Extract.objects.get(pk=1).get_path()
        self.assertNotEqual(ccl_path,extract_path)
        self.assertTrue(os.path.isfile(ccl_path))
        self.assertTrue(os.path.isfile(extract_path))
        
    def test_add_note(self):
        """To test add note for tutorial."""
        user1 = ProfileFactory().user
        self.client.login(username=user1.username, password='hostel77')

        # add note
        result = self.client.post(
            reverse('zds.tutorial.views.answer') +
            '?tutorial={0}'.format(
                self.minituto.pk),
            {
                'last_note': '0',
                'text': u'Histoire de blablater dans les comms du tuto'},
            follow=False)
        self.assertEqual(result.status_code, 302)

        # check notes's number
        self.assertEqual(Note.objects.all().count(), 1)

        # check values
        tuto = Tutorial.objects.get(pk=self.minituto.pk)
        self.assertEqual(Note.objects.get(pk=1).tutorial, tuto)
        self.assertEqual(Note.objects.get(pk=1).author.pk, user1.pk)
        self.assertEqual(Note.objects.get(pk=1).position, 1)
        self.assertEqual(Note.objects.get(pk=1).pk, tuto.last_note.pk)
        self.assertEqual(
            Note.objects.get(
                pk=1).text,
            u'Histoire de blablater dans les comms du tuto')

        # test antispam return 403
        result = self.client.post(
            reverse('zds.tutorial.views.answer') +
            '?tutorial={0}'.format(
                self.minituto.pk),
            {
                'last_note': tuto.last_note.pk,
                'text': u'Histoire de tester l\'antispam'},
            follow=False)
        self.assertEqual(result.status_code, 403)

        NoteFactory(
            tutorial=self.minituto,
            position=2,
            author=self.staff)

        # test more note
        result = self.client.post(
            reverse('zds.tutorial.views.answer') +
            '?tutorial={0}'.format(
                self.minituto.pk),
            {
                'last_note': self.minituto.last_note.pk,
                'text': u'Histoire de tester l\'antispam'},
            follow=False)
        self.assertEqual(result.status_code, 302)

    def test_edit_note(self):
        """To test all aspects of the edition of note."""
        user1 = ProfileFactory().user
        self.client.login(username=user1.username, password='hostel77')

        note1 = NoteFactory(
            tutorial=self.minituto,
            position=1,
            author=self.user)
        note2 = NoteFactory(tutorial=self.minituto, position=2, author=user1)

        # normal edit
        result = self.client.post(
            reverse('zds.tutorial.views.edit_note') +
            '?message={0}'.format(
                note2.pk),
            {
                'text': u'Autre texte'},
            follow=False)
        self.assertEqual(result.status_code, 302)

        # check note's number
        self.assertEqual(Note.objects.all().count(), 2)

        # check note
        self.assertEqual(Note.objects.get(pk=note1.pk).tutorial, self.minituto)
        self.assertEqual(Note.objects.get(pk=note2.pk).tutorial, self.minituto)
        self.assertEqual(Note.objects.get(pk=note2.pk).text, u'Autre texte')
        self.assertEqual(Note.objects.get(pk=note2.pk).editor, user1)

        # simple member want edit other note
        result = self.client.post(
            reverse('zds.tutorial.views.edit_note') +
            '?message={0}'.format(
                note1.pk),
            {
                'text': u'Autre texte'},
            follow=False)
        self.assertEqual(result.status_code, 403)
        self.assertNotEqual(Note.objects.get(pk=note1.pk).editor, user1)

        # staff want edit other note
        self.client.login(username=self.staff.username, password='hostel77')
        result = self.client.post(
            reverse('zds.tutorial.views.edit_note') +
            '?message={0}'.format(
                note1.pk),
            {
                'text': u'Autre texte'},
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Note.objects.get(pk=note1.pk).editor, self.staff)

    def test_quote_note(self):
        """check quote of note."""
        user1 = ProfileFactory().user
        self.client.login(username=user1.username, password='hostel77')

        NoteFactory(
            tutorial=self.minituto,
            position=1,
            author=self.user)
        NoteFactory(tutorial=self.minituto, position=2, author=user1)
        note3 = NoteFactory(
            tutorial=self.minituto,
            position=3,
            author=self.user)

        # normal quote => true
        result = self.client.get(
            reverse('zds.tutorial.views.answer') +
            '?tutorial={0}&cite={1}'.format(
                self.minituto.pk,
                note3.pk),
            follow=False)
        self.assertEqual(result.status_code, 200)

        # quote on anstispamm => false
        NoteFactory(tutorial=self.minituto, position=4, author=user1)
        result = self.client.get(
            reverse('zds.tutorial.views.answer') +
            '?tutorial={0}&cite={1}'.format(
                self.minituto.pk,
                note3.pk),
            follow=False)
        self.assertEqual(result.status_code, 403)

    def test_like_note(self):
        """check like a note for tuto."""
        user1 = ProfileFactory().user
        self.client.login(username=user1.username, password='hostel77')

        note1 = NoteFactory(
            tutorial=self.minituto,
            position=1,
            author=self.user)
        note2 = NoteFactory(tutorial=self.minituto, position=2, author=user1)
        note3 = NoteFactory(
            tutorial=self.minituto,
            position=3,
            author=self.user)

        # normal like
        result = self.client.get(
            reverse('zds.tutorial.views.like_note') +
            '?message={0}'.format(
                note3.pk),
            follow=True)
        self.assertEqual(result.status_code, 200)

        self.assertEqual(Note.objects.get(pk=note1.pk).like, 0)
        self.assertEqual(Note.objects.get(pk=note2.pk).like, 0)
        self.assertEqual(Note.objects.get(pk=note3.pk).like, 1)

        # like yourself
        result = self.client.get(
            reverse('zds.tutorial.views.like_note') +
            '?message={0}'.format(
                note2.pk),
            follow=True)
        self.assertEqual(result.status_code, 200)

        self.assertEqual(Note.objects.get(pk=note1.pk).like, 0)
        self.assertEqual(Note.objects.get(pk=note2.pk).like, 0)
        self.assertEqual(Note.objects.get(pk=note3.pk).like, 1)

        # re-like a post
        result = self.client.get(
            reverse('zds.tutorial.views.like_note') +
            '?message={0}'.format(
                note3.pk),
            follow=True)
        self.assertEqual(result.status_code, 200)

        self.assertEqual(Note.objects.get(pk=note1.pk).like, 0)
        self.assertEqual(Note.objects.get(pk=note2.pk).like, 0)
        self.assertEqual(Note.objects.get(pk=note3.pk).like, 0)

    def test_dislike_note(self):
        """check like a note for tuto."""
        user1 = ProfileFactory().user
        self.client.login(username=user1.username, password='hostel77')

        note1 = NoteFactory(
            tutorial=self.minituto,
            position=1,
            author=self.user)
        note2 = NoteFactory(tutorial=self.minituto, position=2, author=user1)
        note3 = NoteFactory(
            tutorial=self.minituto,
            position=3,
            author=self.user)

        # normal like
        result = self.client.get(
            reverse('zds.tutorial.views.dislike_note') +
            '?message={0}'.format(
                note3.pk),
            follow=True)
        self.assertEqual(result.status_code, 200)

        self.assertEqual(Note.objects.get(pk=note1.pk).dislike, 0)
        self.assertEqual(Note.objects.get(pk=note2.pk).dislike, 0)
        self.assertEqual(Note.objects.get(pk=note3.pk).dislike, 1)

        # like yourself
        result = self.client.get(
            reverse('zds.tutorial.views.dislike_note') +
            '?message={0}'.format(
                note2.pk),
            follow=True)
        self.assertEqual(result.status_code, 200)

        self.assertEqual(Note.objects.get(pk=note1.pk).dislike, 0)
        self.assertEqual(Note.objects.get(pk=note2.pk).dislike, 0)
        self.assertEqual(Note.objects.get(pk=note3.pk).dislike, 1)

        # re-like a post
        result = self.client.get(
            reverse('zds.tutorial.views.dislike_note') +
            '?message={0}'.format(
                note3.pk),
            follow=True)
        self.assertEqual(result.status_code, 200)

        self.assertEqual(Note.objects.get(pk=note1.pk).dislike, 0)
        self.assertEqual(Note.objects.get(pk=note2.pk).dislike, 0)
        self.assertEqual(Note.objects.get(pk=note3.pk).dislike, 0)

    def test_import_tuto(self):
        """Test import of big tuto."""
        result = self.client.post(
            reverse('zds.tutorial.views.import_tuto'),
            {
                'file': open(
                    os.path.join(
                        settings.SITE_ROOT,
                        'fixtures',
                        'tuto',
                        'temps-reel-avec-irrlicht',
                        'temps-reel-avec-irrlicht.tuto'),
                    'r'),
                'images': open(
                    os.path.join(
                        settings.SITE_ROOT,
                        'fixtures',
                        'tuto',
                        'temps-reel-avec-irrlicht',
                        'images.zip'),
                    'r')},
            follow=False)
        self.assertEqual(result.status_code, 302)

        self.assertEqual(Tutorial.objects.all().count(), 2)

    def test_url_for_guest(self):
        """Test simple get request by guest."""

        # logout before
        self.client.logout()

        # guest can read public tutorials
        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_tutorial_online',
                args=[
                    self.minituto.pk,
                    self.minituto.slug]),
            follow=True)
        self.assertEqual(result.status_code, 200)

        # guest can't read offline tutorials
        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_tutorial',
                args=[
                    self.minituto.pk,
                    self.minituto.slug]),
            follow=False)
        self.assertEqual(result.status_code, 302)

    def test_url_for_member(self):
        """Test simple get request by simple member."""

        # logout before
        self.client.logout()
        # login with simple member
        self.assertEqual(
            self.client.login(
                username=self.user.username,
                password='hostel77'),
            True)

        # member who isn't author can read public tutorials
        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_tutorial_online',
                args=[
                    self.minituto.pk,
                    self.minituto.slug]),
            follow=True)
        self.assertEqual(result.status_code, 200)

        # member who isn't author  can't read offline tutorials
        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_tutorial',
                args=[
                    self.minituto.pk,
                    self.minituto.slug]),
            follow=True)
        self.assertEqual(result.status_code, 403)

    def test_url_for_author(self):
        """Test simple get request by author."""

        # logout before
        self.client.logout()
        # login with simple member
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)

        # member who isn't author can read public tutorials
        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_tutorial_online',
                args=[
                    self.minituto.pk,
                    self.minituto.slug]),
            follow=True)
        self.assertEqual(result.status_code, 200)

        # member who isn't author  can't read offline tutorials
        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_tutorial',
                args=[
                    self.minituto.pk,
                    self.minituto.slug]),
            follow=True)
        self.assertEqual(result.status_code, 200)

    def test_url_for_staff(self):
        """Test simple get request by staff."""

        # logout before
        self.client.logout()
        # login with simple member
        self.assertEqual(
            self.client.login(
                username=self.staff.username,
                password='hostel77'),
            True)

        # member who isn't author can read public tutorials
        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_tutorial_online',
                args=[
                    self.minituto.pk,
                    self.minituto.slug]),
            follow=True)
        self.assertEqual(result.status_code, 200)

        # member who isn't author  can't read offline tutorials
        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_tutorial',
                args=[
                    self.minituto.pk,
                    self.minituto.slug]),
            follow=True)
        self.assertEqual(result.status_code, 200)

    def test_alert(self):
        user1 = ProfileFactory().user
        note = NoteFactory(tutorial=self.minituto, author=user1, position=1)
        login_check = self.client.login(
            username=self.user.username,
            password='hostel77')
        self.assertEqual(login_check, True)
        # signal note
        result = self.client.post(
            reverse('zds.tutorial.views.edit_note') +
            '?message={0}'.format(
                note.pk),
            {
                'signal_text': 'Troll',
                'signal_message': 'Confirmer',
            },
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Alert.objects.all().count(), 1)

        # connect with staff
        login_check = self.client.login(
            username=self.staff.username,
            password='hostel77')
        self.assertEqual(login_check, True)
        # solve alert
        result = self.client.post(
            reverse('zds.tutorial.views.solve_alert'),
            {
                'alert_pk': Alert.objects.first().pk,
                'text': 'Ok',
                'delete_message': 'Resoudre',
            },
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Alert.objects.all().count(), 0)
        self.assertEqual(
            PrivateTopic.objects.filter(
                author=self.user).count(),
            1)
        self.assertEquals(len(mail.outbox), 0)

    def tearDown(self):
        if os.path.isdir(settings.REPO_PATH):
            shutil.rmtree(settings.REPO_PATH)
        if os.path.isdir(settings.REPO_PATH_PROD):
            shutil.rmtree(settings.REPO_PATH_PROD)
        if os.path.isdir(settings.REPO_ARTICLE_PATH):
            shutil.rmtree(settings.REPO_ARTICLE_PATH)
        if os.path.isdir(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)
