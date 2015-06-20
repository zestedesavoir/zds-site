# coding: utf-8

import os
import shutil
import tempfile
import zipfile
import datetime

from git import Repo
from zds.utils.tutorials import GetPublished

try:
    import ujson as json_reader
except:
    try:
        import simplejson as json_reader
    except:
        import json as json_reader
from django.db.models import Q
from django.contrib.auth.models import Group
from django.conf import settings
from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings
from django.contrib import messages

from zds.forum.factories import CategoryFactory, ForumFactory
from zds.member.factories import ProfileFactory, StaffProfileFactory
from zds.gallery.factories import UserGalleryFactory, ImageFactory
from zds.mp.models import PrivateTopic
from zds.forum.models import Topic
from zds.settings import BASE_DIR
from zds.tutorial.factories import BigTutorialFactory, MiniTutorialFactory, PartFactory, ChapterFactory, \
    NoteFactory, SubCategoryFactory, LicenceFactory, ExtractFactory
from zds.gallery.factories import GalleryFactory
from zds.tutorial.models import Note, Tutorial, Validation, Extract, Part, Chapter
from zds.tutorial.views import insert_into_zip
from zds.utils.models import SubCategory, Licence, Alert, HelpWriting
from zds.utils.misc import compute_hash


overrided_zds_app = settings.ZDS_APP
overrided_zds_app['tutorial']['repo_path'] = os.path.join(BASE_DIR, 'tutoriels-private-test')
overrided_zds_app['tutorial']['repo_public_path'] = os.path.join(BASE_DIR, 'tutoriels-public-test')
overrided_zds_app['article']['repo_path'] = os.path.join(BASE_DIR, 'article-data-test')


@override_settings(MEDIA_ROOT=os.path.join(BASE_DIR, 'media-test'))
@override_settings(ZDS_APP=overrided_zds_app)
class BigTutorialTests(TestCase):

    def setUp(self):

        settings.EMAIL_BACKEND = \
            'django.core.mail.backends.locmem.EmailBackend'
        self.mas = ProfileFactory().user
        settings.ZDS_APP['member']['bot_account'] = self.mas.username

        self.user_author = ProfileFactory().user
        self.user = ProfileFactory().user
        self.staff = StaffProfileFactory().user
        self.subcat = SubCategoryFactory()

        ForumFactory(
            pk=settings.ZDS_APP['forum']['beta_forum_id'],
            category=CategoryFactory(position=1),
            position_in_category=1)
        self.licence = LicenceFactory()
        self.licence.save()

        self.bigtuto = BigTutorialFactory(light=True)
        self.bigtuto.authors.add(self.user_author)
        self.bigtuto.gallery = GalleryFactory()
        self.bigtuto.licence = self.licence
        self.bigtuto.save()

        self.part1 = PartFactory(tutorial=self.bigtuto, position_in_tutorial=1, light=True)
        self.part2 = PartFactory(tutorial=self.bigtuto, position_in_tutorial=2, light=True)
        self.part3 = PartFactory(tutorial=self.bigtuto, position_in_tutorial=3, light=True)

        self.chapter1_1 = ChapterFactory(
            part=self.part1,
            position_in_part=1,
            position_in_tutorial=1,
            light=True)
        self.chapter1_2 = ChapterFactory(
            part=self.part1,
            position_in_part=2,
            position_in_tutorial=2,
            light=True)
        self.chapter1_3 = ChapterFactory(
            part=self.part1,
            position_in_part=3,
            position_in_tutorial=3,
            light=True)

        self.chapter2_1 = ChapterFactory(
            part=self.part2,
            position_in_part=1,
            position_in_tutorial=4,
            light=True)
        self.chapter2_2 = ChapterFactory(
            part=self.part2,
            position_in_part=2,
            position_in_tutorial=5,
            light=True)

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
                'version': self.bigtuto.sha_draft,
                'source': 'http://zestedesavoir.com',
            },
            follow=False)
        self.assertEqual(pub.status_code, 302)

        # reserve tutorial
        validation = Validation.objects.get(
            tutorial__pk=self.bigtuto.pk)
        pub = self.client.post(
            reverse('zds.tutorial.views.reservation', args=[validation.pk]),
            follow=False)
        self.assertEqual(pub.status_code, 302)
        self.first_validator = self.staff

        # publish tutorial
        pub = self.client.post(
            reverse('zds.tutorial.views.valid_tutorial'),
            {
                'tutorial': self.bigtuto.pk,
                'text': u'Ce tuto est excellent',
                'is_major': True,
                'source': 'http://zestedesavoir.com',
            },
            follow=False)
        self.bigtuto = Tutorial.objects.get(pk=self.bigtuto.pk)
        self.assertEqual(pub.status_code, 302)
        self.assertEquals(len(mail.outbox), 1)

        mail.outbox = []

    def create_basic_big_tutorial(self):
        future_tutorial = BigTutorialFactory()
        future_tutorial.authors.add(self.user_author)
        future_tutorial.gallery = GalleryFactory()
        future_tutorial.licence = self.licence
        future_tutorial.save()

        part1 = PartFactory(tutorial=future_tutorial, position_in_tutorial=1)
        part2 = PartFactory(tutorial=future_tutorial, position_in_tutorial=2)
        PartFactory(tutorial=future_tutorial, position_in_tutorial=3)

        ChapterFactory(
            part=part1,
            position_in_part=1,
            position_in_tutorial=1)
        ChapterFactory(
            part=part1,
            position_in_part=2,
            position_in_tutorial=2)
        ChapterFactory(
            part=part1,
            position_in_part=3,
            position_in_tutorial=3)

        ChapterFactory(
            part=part2,
            position_in_part=1,
            position_in_tutorial=4)
        ChapterFactory(
            part=part2,
            position_in_part=2,
            position_in_tutorial=5)

        return future_tutorial

    def test_public_tutorial(self):
        future_tutorial = self.create_basic_big_tutorial()

        staff = StaffProfileFactory().user

        login_check = self.client.login(
            username=staff.username,
            password='hostel77')
        self.assertEqual(login_check, True)

        # ask public tutorial
        pub = self.client.post(
            reverse('zds.tutorial.views.ask_validation'),
            {
                'tutorial': future_tutorial.pk,
                'text': u'Ce tuto est excellent',
                'version': future_tutorial.sha_draft,
                'source': 'http://zestedesavoir.com',
            },
            follow=False)
        self.assertEqual(pub.status_code, 302)

        # reserve tutorial
        validation = Validation.objects.get(
            tutorial__pk=future_tutorial.pk)
        pub = self.client.post(
            reverse('zds.tutorial.views.reservation', args=[validation.pk]),
            follow=False)
        self.assertEqual(pub.status_code, 302)

        # publish tutorial
        pub = self.client.post(
            reverse('zds.tutorial.views.valid_tutorial'),
            {
                'tutorial': future_tutorial.pk,
                'text': u'Ce tuto est excellent',
                'is_major': True,
                'source': 'http://zestedesavoir.com',
            },
            follow=False)
        self.assertEqual(pub.status_code, 302)
        self.assertEquals(len(mail.outbox), 1)

    def test_delete_tutorial_never_beta(self):
        future_tutorial = self.create_basic_big_tutorial()
        future_tutorial_pk = future_tutorial.pk

        login_check = self.client.login(
            username=self.user_author.username,
            password='hostel77')
        self.assertEqual(login_check, True)

        # delete tutorial
        response = self.client.post(
            reverse('zds.tutorial.views.delete_tutorial', args=[future_tutorial_pk]),
            {},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(Tutorial.objects.filter(pk=future_tutorial_pk).first())

    def test_delete_tutorial_on_beta(self):
        future_tutorial = self.create_basic_big_tutorial()
        future_tutorial_pk = future_tutorial.pk

        login_check = self.client.login(
            username=self.user_author.username,
            password='hostel77')
        self.assertEqual(login_check, True)

        # then active the beta on tutorial
        self.assertIsNone(Topic.objects.get_beta_topic_of(future_tutorial))
        sha_draft = Tutorial.objects.get(pk=future_tutorial_pk).sha_draft
        self.client.post(
            reverse('zds.tutorial.views.modify_tutorial'),
            {
                'tutorial': future_tutorial_pk,
                'activ_beta': True,
                'version': sha_draft
            },
            follow=False
        )
        topic = Topic.objects.get_beta_topic_of(future_tutorial)
        self.assertIsNotNone(topic)
        topic_pk = topic.pk
        # delete tutorial
        self.client.post(
            reverse('zds.tutorial.views.delete_tutorial', args=[future_tutorial_pk]),
            {},
            follow=False
        )
        self.assertIsNone(Tutorial.objects.filter(pk=future_tutorial_pk).first())
        self.assertIsNone(Topic.objects.filter(pk=topic_pk).first())

    def test_delete_tutorial_on_desactivate_beta(self):
        future_tutorial = self.create_basic_big_tutorial()
        future_tutorial_pk = future_tutorial.pk

        login_check = self.client.login(
            username=self.user_author.username,
            password='hostel77')
        self.assertEqual(login_check, True)

        # then active the beta on tutorial
        self.assertIsNone(Topic.objects.get_beta_topic_of(future_tutorial))
        sha_draft = Tutorial.objects.get(pk=future_tutorial_pk).sha_draft
        self.client.post(
            reverse('zds.tutorial.views.modify_tutorial'),
            {
                'tutorial': future_tutorial_pk,
                'activ_beta': True,
                'version': sha_draft
            },
            follow=False
        )
        topic = Topic.objects.get_beta_topic_of(future_tutorial)
        self.assertIsNotNone(topic)
        topic_pk = topic.pk
        # then desactive the beta on tutorial
        self.assertIsNone(Topic.objects.filter(pk=topic_pk, is_locked=True).first())
        sha_draft = Tutorial.objects.get(pk=future_tutorial_pk).sha_draft
        self.client.post(
            reverse('zds.tutorial.views.modify_tutorial'),
            {
                'tutorial': future_tutorial_pk,
                'desactiv_beta': True,
                'version': sha_draft
            },
            follow=False
        )
        self.assertIsNotNone(Topic.objects.filter(pk=topic_pk, is_locked=True).first())
        # delete tutorial
        self.client.post(
            reverse('zds.tutorial.views.delete_tutorial', args=[future_tutorial_pk]),
            {},
            follow=False
        )
        self.assertIsNone(Tutorial.objects.filter(pk=future_tutorial_pk).first())
        self.assertIsNone(Topic.objects.filter(pk=topic_pk).first())

    def test_import_archive(self):
        login_check = self.client.login(
            username=self.user_author.username,
            password='hostel77')
        self.assertEqual(login_check, True)
        # create temporary data directory
        temp = os.path.join(tempfile.gettempdir(), "temp")
        if not os.path.exists(temp):
            os.makedirs(temp, mode=0777)
        # download zip
        repo_path = os.path.join(settings.ZDS_APP['tutorial']['repo_path'], self.bigtuto.get_phy_slug())
        repo = Repo(repo_path)
        zip_path = os.path.join(tempfile.gettempdir(), self.bigtuto.slug + '.zip')
        zip_file = zipfile.ZipFile(zip_path, 'w')
        insert_into_zip(zip_file, repo.commit(self.bigtuto.sha_draft).tree)
        zip_file.close()

        zip_dir = os.path.join(temp, self.bigtuto.get_phy_slug())
        if not os.path.exists(zip_dir):
            os.makedirs(zip_dir, mode=0777)

        # Extract zip
        with zipfile.ZipFile(zip_path) as zip_file:
            for member in zip_file.namelist():
                filename = os.path.basename(member)
                # skip directories
                if not filename:
                    continue
                if not os.path.exists(os.path.dirname(os.path.join(zip_dir, member))):
                    os.makedirs(os.path.dirname(os.path.join(zip_dir, member)), mode=0777)
                # copy file (taken from zipfile's extract)
                source = zip_file.open(member)
                target = file(os.path.join(zip_dir, filename), "wb")
                with source, target:
                    shutil.copyfileobj(source, target)
        self.assertTrue(os.path.isdir(zip_dir))

        # update markdown files
        up_intro_tfile = open(os.path.join(temp, self.bigtuto.get_phy_slug(), self.bigtuto.introduction), "a")
        up_intro_tfile.write(u"preuve de modification de l'introduction")
        up_intro_tfile.close()
        up_conclu_tfile = open(os.path.join(temp, self.bigtuto.get_phy_slug(), self.bigtuto.conclusion), "a")
        up_conclu_tfile.write(u"preuve de modification de la conclusion")
        up_conclu_tfile.close()
        parts = Part.objects.filter(tutorial__pk=self.bigtuto.pk)
        for part in parts:
            up_intro_pfile = open(os.path.join(temp, self.bigtuto.get_phy_slug(), part.introduction), "a")
            up_intro_pfile.write(u"preuve de modification de l'introduction")
            up_intro_pfile.close()
            up_conclu_pfile = open(os.path.join(temp, self.bigtuto.get_phy_slug(), part.conclusion), "a")
            up_conclu_pfile.write(u"preuve de modification de la conclusion")
            up_conclu_pfile.close()
            chapters = Chapter.objects.filter(part__pk=part.pk)
            for chapter in chapters:
                up_intro_cfile = open(os.path.join(temp, self.bigtuto.get_phy_slug(), chapter.introduction), "a")
                up_intro_cfile.write(u"preuve de modification de l'introduction")
                up_intro_cfile.close()
                up_conclu_cfile = open(os.path.join(temp, self.bigtuto.get_phy_slug(), chapter.conclusion), "a")
                up_conclu_cfile.write(u"preuve de modification de la conclusion")
                up_conclu_cfile.close()

        # zip directory
        shutil.make_archive(os.path.join(temp, self.bigtuto.get_phy_slug()),
                            "zip",
                            os.path.join(temp, self.bigtuto.get_phy_slug()))

        self.assertTrue(os.path.isfile(os.path.join(temp, self.bigtuto.get_phy_slug() + ".zip")))

        # import zip archive
        result = self.client.post(
            reverse('zds.tutorial.views.import_tuto'),
            {
                'file': open(
                    os.path.join(
                        temp,
                        os.path.join(temp, self.bigtuto.get_phy_slug() + ".zip")),
                    'r'),
                'tutorial': self.bigtuto.pk,
                'import-archive': "importer"},
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Tutorial.objects.all().count(), 1)

        # delete temporary data directory
        shutil.rmtree(temp)
        os.remove(zip_path)

    def test_fail_import_archive(self):

        login_check = self.client.login(
            username=self.user_author.username,
            password='hostel77')
        self.assertEqual(login_check, True)

        temp = os.path.join(tempfile.gettempdir(), "temp")
        if not os.path.exists(temp):
            os.makedirs(temp, mode=0777)

        # test fail import
        with open(os.path.join(temp, 'test.py'), 'a') as f:
            f.write('something')

        result = self.client.post(
            reverse('zds.tutorial.views.import_tuto'),
            {
                'file': open(
                    os.path.join(
                        temp,
                        'test.py'),
                    'r'),
                'tutorial': self.bigtuto.pk,
                'import-archive': "importer"},
            follow=False
        )
        self.assertEqual(result.status_code, 200)

        # delete temporary data directory
        shutil.rmtree(temp)

    def test_add_note(self):
        """To test add note for tutorial."""
        user1 = ProfileFactory().user
        self.client.login(username=user1.username, password='hostel77')

        # add note with no text = try again !
        result = self.client.post(
            reverse('zds.tutorial.views.answer') +
            '?tutorial={0}'.format(
                self.bigtuto.pk),
            {
                'last_note': '0',
                'text': u''},
            follow=False)
        self.assertEqual(result.status_code, 200)
        # check notes's number
        self.assertEqual(Note.objects.all().count(), 0)

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
        first_tuto = Note.objects.first()
        self.assertEqual(first_tuto.tutorial, tuto)
        self.assertEqual(first_tuto.author.pk, user1.pk)
        self.assertEqual(first_tuto.position, 1)
        self.assertEqual(first_tuto.pk, tuto.last_note.pk)
        self.assertEqual(
            first_tuto.text,
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
                        settings.BASE_DIR,
                        'fixtures',
                        'tuto',
                        'temps-reel-avec-irrlicht',
                        'temps-reel-avec-irrlicht.tuto'),
                    'r'),
                'images': open(
                    os.path.join(
                        settings.BASE_DIR,
                        'fixtures',
                        'tuto',
                        'temps-reel-avec-irrlicht',
                        'images.zip'),
                    'r'),
                'import-tuto': "importer"},
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
                    self.part2.pk,
                    self.part2.slug]),
            follow=True)
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse('zds.tutorial.views.view_chapter_online',
                    args=[self.bigtuto.pk,
                          self.bigtuto.slug,
                          self.part2.pk,
                          self.part2.slug,
                          self.chapter2_1.pk,
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
                    self.part2.pk,
                    self.part2.slug]),
            follow=False)
        self.assertEqual(result.status_code, 302)

        result = self.client.get(
            reverse('zds.tutorial.views.view_chapter',
                    args=[self.bigtuto.pk,
                          self.bigtuto.slug,
                          self.part2.pk,
                          self.part2.slug,
                          self.chapter2_1.pk,
                          self.chapter2_1.slug]),
            follow=False)
        self.assertEqual(result.status_code, 302)

    def test_workflow_tuto(self):
        """Test workflow of tutorial."""

        ForumFactory(
            category=CategoryFactory(position=1),
            position_in_category=1)

        # logout before
        self.client.logout()
        # login with simple member
        self.assertEqual(
            self.client.login(
                username=self.user.username,
                password='hostel77'),
            True)

        # add new big tuto
        result = self.client.post(
            reverse('zds.tutorial.views.add_tutorial'),
            {
                'title': u"Introduction à l'algèbre",
                'description': "Perçer les mystère de boole",
                'introduction': "Bienvenue dans le monde binaires",
                'conclusion': "",
                'type': "BIG",
                'licence': self.licence.pk,
                'subcategory': self.subcat.pk,
            },
            follow=False)

        self.assertEqual(result.status_code, 302)
        self.assertEqual(Tutorial.objects.all().count(), 2)
        tuto = Tutorial.objects.last()
        # add part 1
        result = self.client.post(
            reverse('zds.tutorial.views.add_part') + '?tutoriel={}'.format(tuto.pk),
            {
                'title': u"Partie 1",
                'introduction': u"Présentation",
                'conclusion': u"Fin de la présentation",
                'msg_commit': u"Initialisation de ma partie 1"
            },
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Part.objects.filter(tutorial=tuto).count(), 1)
        p1 = Part.objects.filter(tutorial=tuto).last()

        # check view offline
        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_part',
                args=[
                    tuto.pk,
                    tuto.slug,
                    p1.pk,
                    p1.slug]),
            follow=True)
        self.assertContains(response=result, text=u"Présentation")
        self.assertContains(response=result, text=u"Fin de la présentation")

        # add part 2
        result = self.client.post(
            reverse('zds.tutorial.views.add_part') + '?tutoriel={}'.format(tuto.pk),
            {
                'title': u"Partie 2",
                'introduction': u"Analyse",
                'conclusion': u"Fin de l'analyse",
                'msg_commit': u"Initialisation de ma partie 2"
            },
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Part.objects.filter(tutorial=tuto).count(), 2)
        p2 = Part.objects.filter(tutorial=tuto).last()
        self.assertEqual(u"Analyse", p2.get_introduction())
        # check view offline
        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_part',
                args=[
                    tuto.pk,
                    tuto.slug,
                    p2.pk,
                    p2.slug]),
            follow=True)
        self.assertContains(response=result, text=u"Analyse")
        self.assertContains(response=result, text=u"Fin de l'analyse")

        # add part 3
        result = self.client.post(
            reverse('zds.tutorial.views.add_part') + '?tutoriel={}'.format(tuto.pk),
            {
                'title': u"Partie 2",
                'introduction': "Expérimentation",
                'conclusion': "C'est terminé",
                'msg_commit': u"Initialisation de ma partie 3"
            },
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Part.objects.filter(tutorial=tuto).count(), 3)
        p3 = Part.objects.filter(tutorial=tuto).last()

        # check view offline
        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_part',
                args=[
                    tuto.pk,
                    tuto.slug,
                    p3.pk,
                    p3.slug]),
            follow=True)
        self.assertContains(response=result, text=u"Expérimentation")
        self.assertContains(response=result, text=u"C'est terminé")

        # add chapter 1 for part 2
        result = self.client.post(
            reverse('zds.tutorial.views.add_chapter') + '?partie={}'.format(p2.pk),
            {
                'title': u"Chapitre 1",
                'introduction': "Mon premier chapitre",
                'conclusion': "Fin de mon premier chapitre",
                'msg_commit': u"Initialisation du chapitre 1"
            },
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Chapter.objects.filter(part=p1).count(), 0)
        self.assertEqual(Chapter.objects.filter(part=p2).count(), 1)
        self.assertEqual(Chapter.objects.filter(part=p3).count(), 0)
        c1 = Chapter.objects.filter(part=p2).last()

        # check view offline
        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_chapter',
                args=[
                    tuto.pk,
                    tuto.slug,
                    p2.pk,
                    p2.slug,
                    c1.pk,
                    c1.slug]),
            follow=True)
        self.assertContains(response=result, text=u"Mon premier chapitre")
        self.assertContains(response=result, text=u"Fin de mon premier chapitre")

        # add chapter 2 for part 2
        result = self.client.post(
            reverse('zds.tutorial.views.add_chapter') + '?partie={}'.format(p2.pk),
            {
                'title': u"Chapitre 2",
                'introduction': u"Mon deuxième chapitre",
                'conclusion': u"Fin de mon deuxième chapitre",
                'msg_commit': u"Initialisation du chapitre 2"
            },
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Chapter.objects.filter(part=p1).count(), 0)
        self.assertEqual(Chapter.objects.filter(part=p2).count(), 2)
        self.assertEqual(Chapter.objects.filter(part=p3).count(), 0)
        c2 = Chapter.objects.filter(part=p2).last()

        # check view offline
        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_chapter',
                args=[
                    tuto.pk,
                    tuto.slug,
                    p2.pk,
                    p2.slug,
                    c2.pk,
                    c2.slug]),
            follow=True)
        self.assertContains(response=result, text=u"Mon deuxième chapitre")
        self.assertContains(response=result, text=u"Fin de mon deuxième chapitre")

        # add chapter 3 for part 2
        result = self.client.post(
            reverse('zds.tutorial.views.add_chapter') + '?partie={}'.format(p2.pk),
            {
                'title': u"Chapitre 2",
                'introduction': u"Mon troisième chapitre homonyme",
                'conclusion': u"Fin de mon troisième chapitre",
                'msg_commit': u"Initialisation du chapitre 3"
            },
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Chapter.objects.filter(part=p1).count(), 0)
        self.assertEqual(Chapter.objects.filter(part=p2).count(), 3)
        self.assertEqual(Chapter.objects.filter(part=p3).count(), 0)
        c3 = Chapter.objects.filter(part=p2).last()

        # check view offline
        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_chapter',
                args=[
                    tuto.pk,
                    tuto.slug,
                    p2.pk,
                    p2.slug,
                    c3.pk,
                    c3.slug]),
            follow=True)
        self.assertContains(response=result, text=u"Mon troisième chapitre homonyme")
        self.assertContains(response=result, text=u"Fin de mon troisième chapitre")

        # add chapter 4 for part 1
        result = self.client.post(
            reverse('zds.tutorial.views.add_chapter') + '?partie={}'.format(p1.pk),
            {
                'title': u"Chapitre 1",
                'introduction': "Mon premier chapitre d'une autre partie",
                'conclusion': "",
                'msg_commit': u"Initialisation du chapitre 4"
            },
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Chapter.objects.filter(part=p1).count(), 1)
        self.assertEqual(Chapter.objects.filter(part=p2).count(), 3)
        self.assertEqual(Chapter.objects.filter(part=p3).count(), 0)
        c4 = Chapter.objects.filter(part=p1).last()

        # check view offline
        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_chapter',
                args=[
                    tuto.pk,
                    tuto.slug,
                    p1.pk,
                    p1.slug,
                    c4.pk,
                    c4.slug]),
            follow=True)
        self.assertContains(response=result, text=u"Mon premier chapitre d'une autre partie")

        # add extract 1 of chapter 3
        result = self.client.post(
            reverse('zds.tutorial.views.add_extract') + '?chapitre={}'.format(c3.pk),
            {
                'title': u"Extrait 1",
                'text': "Prune",
                'msg_commit': u"Initialisation de l'extrait 1"
            },
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Extract.objects.filter(chapter=c3).count(), 1)
        e1 = Extract.objects.filter(chapter=c3).last()

        # add extract 2 of chapter 3
        result = self.client.post(
            reverse('zds.tutorial.views.add_extract') + '?chapitre={}'.format(c3.pk),
            {
                'title': u"Extrait 2",
                'text': "Citron",
                'msg_commit': u"Initialisation de l'extrait 2"
            },
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Extract.objects.filter(chapter=c3).count(), 2)
        e2 = Extract.objects.filter(chapter=c3).last()

        # add extract 3 of chapter 2
        result = self.client.post(
            reverse('zds.tutorial.views.add_extract') + '?chapitre={}'.format(c2.pk),
            {
                'title': u"Extrait 3",
                'text': "Kiwi",
                'msg_commit': u"Initialisation de l'extrait 3"
            },
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Extract.objects.filter(chapter=c2).count(), 1)
        e3 = Extract.objects.filter(chapter=c2).last()

        # check content edit part
        result = self.client.get(
            reverse('zds.tutorial.views.edit_part') + "?partie={}".format(p1.pk),
            follow=True)
        self.assertContains(response=result, text=u"Présentation")
        self.assertContains(response=result, text=u"Fin de la présentation")

        result = self.client.get(
            reverse('zds.tutorial.views.edit_part') + "?partie={}".format(p2.pk),
            follow=True)
        self.assertContains(response=result, text=u"Analyse")
        self.assertContains(response=result, text="Fin de l&#39;analyse")

        result = self.client.get(
            reverse('zds.tutorial.views.edit_part') + "?partie={}".format(p3.pk),
            follow=True)
        self.assertContains(response=result, text=u"Expérimentation")
        self.assertContains(response=result, text=u"est terminé")

        # check content edit chapter
        result = self.client.get(
            reverse('zds.tutorial.views.edit_chapter') + "?chapitre={}".format(c1.pk),
            follow=True)
        self.assertContains(response=result, text=u"Chapitre 1")
        self.assertContains(response=result, text=u"Mon premier chapitre")
        self.assertContains(response=result, text=u"Fin de mon premier chapitre")

        result = self.client.get(
            reverse('zds.tutorial.views.edit_chapter') + "?chapitre={}".format(c2.pk),
            follow=True)
        self.assertContains(response=result, text=u"Chapitre 2")
        self.assertContains(response=result, text=u"Mon deuxième chapitre")
        self.assertContains(response=result, text=u"Fin de mon deuxième chapitre")

        result = self.client.get(
            reverse('zds.tutorial.views.edit_chapter') + "?chapitre={}".format(c3.pk),
            follow=True)
        self.assertContains(response=result, text=u"Chapitre 2")
        self.assertContains(response=result, text=u"Mon troisième chapitre homonyme")
        self.assertContains(response=result, text=u"Fin de mon troisième chapitre")

        result = self.client.get(
            reverse('zds.tutorial.views.edit_chapter') + "?chapitre={}".format(c4.pk),
            follow=True)
        self.assertContains(response=result, text=u"Chapitre 1")
        self.assertContains(response=result, text=u"Mon premier chapitre d&#39;une autre partie")

        # check content edit extract
        result = self.client.get(
            reverse('zds.tutorial.views.edit_extract') + "?extrait={}".format(e1.pk),
            follow=True)
        self.assertContains(response=result, text=u"Extrait 1")
        self.assertContains(response=result, text=u"Prune")

        result = self.client.get(
            reverse('zds.tutorial.views.edit_extract') + "?extrait={}".format(e2.pk),
            follow=True)
        self.assertContains(response=result, text=u"Extrait 2")
        self.assertContains(response=result, text=u"Citron")

        result = self.client.get(
            reverse('zds.tutorial.views.edit_extract') + "?extrait={}".format(e3.pk),
            follow=True)
        self.assertContains(response=result, text=u"Extrait 3")
        self.assertContains(response=result, text=u"Kiwi")

        # edit part 2
        result = self.client.post(
            reverse('zds.tutorial.views.edit_part') + '?partie={}'.format(p2.pk),
            {
                'title': u"Partie 2 : edition de titre",
                'introduction': u"Expérimentation : edition d'introduction",
                'conclusion': u"C'est terminé : edition de conlusion",
                'msg_commit': u"Mise à jour de la partie",
                "last_hash": compute_hash([os.path.join(p2.tutorial.get_path(), p2.introduction),
                                           os.path.join(p2.tutorial.get_path(), p2.conclusion)])
            },
            follow=True)
        self.assertContains(response=result, text=u"Partie 2 : edition de titre")
        self.assertContains(response=result, text=u"Expérimentation : edition d'introduction")
        self.assertContains(response=result, text=u"C'est terminé : edition de conlusion")
        self.assertEqual(Part.objects.filter(tutorial=tuto).count(), 3)

        # edit chapter 3
        result = self.client.post(
            reverse('zds.tutorial.views.edit_chapter') + '?chapitre={}'.format(c3.pk),
            {
                'title': u"Chapitre 3 : edition de titre",
                'introduction': u"Edition d'introduction",
                'conclusion': u"Edition de conlusion",
                'msg_commit': u"Mise à jour du chapitre",
                "last_hash": compute_hash([
                    os.path.join(c3.get_path(), "introduction.md"),
                    os.path.join(c3.get_path(), "conclusion.md")])
            },
            follow=True)
        self.assertContains(response=result, text=u"Chapitre 3 : edition de titre")
        self.assertContains(response=result, text=u"Edition d'introduction")
        self.assertContains(response=result, text=u"Edition de conlusion")
        self.assertEqual(Chapter.objects.filter(part=p2.pk).count(), 3)
        p2 = Part.objects.filter(pk=p2.pk).first()

        # edit part 2
        result = self.client.post(
            reverse('zds.tutorial.views.edit_part') + '?partie={}'.format(p2.pk),
            {
                'title': u"Partie 2 : seconde edition de titre",
                'introduction': u"Expérimentation : seconde edition d'introduction",
                'conclusion': u"C'est terminé : seconde edition de conlusion",
                'msg_commit': u"2nd Màj de la partie 2",
                "last_hash": compute_hash([os.path.join(p2.tutorial.get_path(), p2.introduction),
                                           os.path.join(p2.tutorial.get_path(), p2.conclusion)])
            },
            follow=True)
        self.assertContains(response=result, text=u"Partie 2 : seconde edition de titre")
        self.assertContains(response=result, text=u"Expérimentation : seconde edition d'introduction")
        self.assertContains(response=result, text=u"C'est terminé : seconde edition de conlusion")
        self.assertEqual(Part.objects.filter(tutorial=tuto).count(), 3)

        # edit chapter 2
        result = self.client.post(
            reverse('zds.tutorial.views.edit_chapter') + '?chapitre={}'.format(c2.pk),
            {
                'title': u"Chapitre 2 : edition de titre",
                'introduction': u"Edition d'introduction",
                'conclusion': u"Edition de conlusion",
                'msg_commit': u"MàJ du chapitre 2",
                "last_hash": compute_hash([
                    os.path.join(c2.get_path(), "introduction.md"),
                    os.path.join(c2.get_path(), "conclusion.md")])
            },
            follow=True)
        self.assertContains(response=result, text=u"Chapitre 2 : edition de titre")
        self.assertContains(response=result, text=u"Edition d'introduction")
        self.assertContains(response=result, text=u"Edition de conlusion")
        self.assertEqual(Chapter.objects.filter(part=p2.pk).count(), 3)

        # edit extract 2
        result = self.client.post(
            reverse('zds.tutorial.views.edit_extract') + '?extrait={}'.format(e2.pk),
            {
                'title': u"Extrait 2 : edition de titre",
                'text': u"Agrume",
                "last_hash": compute_hash([os.path.join(e2.get_path())])
            },
            follow=True)
        self.assertContains(response=result, text=u"Extrait 2 : edition de titre")
        self.assertContains(response=result, text=u"Agrume")

        # check content edit part
        result = self.client.get(
            reverse('zds.tutorial.views.edit_part') + "?partie={}".format(p1.pk),
            follow=True)
        self.assertContains(response=result, text=u"Présentation")
        self.assertContains(response=result, text=u"Fin de la présentation")

        result = self.client.get(
            reverse('zds.tutorial.views.edit_part') + "?partie={}".format(p2.pk),
            follow=True)
        self.assertContains(response=result, text=u"Partie 2 : seconde edition de titre")
        self.assertContains(response=result, text="Expérimentation : seconde edition d&#39;introduction")
        self.assertContains(response=result, text="C&#39;est terminé : seconde edition de conlusion")

        result = self.client.get(
            reverse('zds.tutorial.views.edit_part') + "?partie={}".format(p3.pk),
            follow=True)
        self.assertContains(response=result, text=u"Expérimentation")
        self.assertContains(response=result, text=u"est terminé")

        # check content edit chapter
        result = self.client.get(
            reverse('zds.tutorial.views.edit_chapter') + "?chapitre={}".format(c1.pk),
            follow=True)
        self.assertContains(response=result, text=u"Chapitre 1")
        self.assertContains(response=result, text=u"Mon premier chapitre")
        self.assertContains(response=result, text=u"Fin de mon premier chapitre")

        result = self.client.get(
            reverse('zds.tutorial.views.edit_chapter') + "?chapitre={}".format(c2.pk),
            follow=True)
        self.assertContains(response=result, text=u"Chapitre 2 : edition de titre")
        self.assertContains(response=result, text=u"Edition d&#39;introduction")
        self.assertContains(response=result, text=u"Edition de conlusion")

        result = self.client.get(
            reverse('zds.tutorial.views.edit_chapter') + "?chapitre={}".format(c3.pk),
            follow=True)
        self.assertContains(response=result, text=u"Chapitre 3 : edition de titre")
        self.assertContains(response=result, text=u"Edition d&#39;introduction")
        self.assertContains(response=result, text=u"Edition de conlusion")

        result = self.client.get(
            reverse('zds.tutorial.views.edit_chapter') + "?chapitre={}".format(c4.pk),
            follow=True)
        self.assertContains(response=result, text=u"Chapitre 1")
        self.assertContains(response=result, text=u"Mon premier chapitre d&#39;une autre partie")

        # check content edit extract
        result = self.client.get(
            reverse('zds.tutorial.views.edit_extract') + "?extrait={}".format(e1.pk),
            follow=True)
        self.assertContains(response=result, text=u"Extrait 1")
        self.assertContains(response=result, text=u"Prune")

        result = self.client.get(
            reverse('zds.tutorial.views.edit_extract') + "?extrait={}".format(e2.pk),
            follow=True)
        self.assertContains(response=result, text=u"Extrait 2 : edition de titre")
        self.assertContains(response=result, text=u"Agrume")

        result = self.client.get(
            reverse('zds.tutorial.views.edit_extract') + "?extrait={}".format(e3.pk),
            follow=True)
        self.assertContains(response=result, text=u"Extrait 3")
        self.assertContains(response=result, text=u"Kiwi")

        # move chapter 1 against 2
        result = self.client.post(
            reverse('zds.tutorial.views.modify_chapter'),
            {
                'chapter': c1.pk,
                'move_target': c2.position_in_part,
            },
            follow=True)
        # move part 1 against 2
        result = self.client.post(
            reverse('zds.tutorial.views.modify_part'),
            {
                'part': p1.pk,
                'move_target': p2.position_in_tutorial,
            },
            follow=True)
        self.assertEqual(Chapter.objects.filter(part__tutorial=tuto.pk).count(), 4)

        # ask public tutorial
        tuto = Tutorial.objects.get(pk=tuto.pk)

        pub = self.client.post(
            reverse('zds.tutorial.views.ask_validation'),
            {
                'tutorial': tuto.pk,
                'text': u'Ce tuto est excellent',
                'version': tuto.sha_draft,
                'source': '',
            },
            follow=False)
        self.assertEqual(pub.status_code, 302)

        # logout before
        self.client.logout()
        # login with staff member
        self.assertEqual(
            self.client.login(
                username=self.staff.username,
                password='hostel77'),
            True)

        # reserve tutorial
        validation = Validation.objects.filter(
            tutorial__pk=tuto.pk).last()
        pub = self.client.post(
            reverse('zds.tutorial.views.reservation', args=[validation.pk]),
            follow=False)
        self.assertEqual(pub.status_code, 302)
        old_validator = self.staff
        old_mps_count = PrivateTopic.objects\
            .filter(Q(author=old_validator) | Q(participants__in=[old_validator]))\
            .count()

        # logout staff before
        self.client.logout()
        # login with simple member
        self.assertEqual(
            self.client.login(
                username=self.user.username,
                password='hostel77'),
            True)

        # ask public tutorial again
        pub = self.client.post(
            reverse('zds.tutorial.views.ask_validation'),
            {
                'tutorial': tuto.pk,
                'text': u'Nouvelle demande de publication',
                'version': tuto.sha_draft,
                'source': 'www.zestedesavoir.com',
            },
            follow=False)
        self.assertEqual(pub.status_code, 302)

        # old validator stay
        validation = Validation.objects.filter(tutorial__pk=tuto.pk).last()
        self.assertEqual(old_validator, validation.validator)

        # new MP for staff
        new_mps_count = PrivateTopic.objects\
            .filter(Q(author=old_validator) | Q(participants__in=[old_validator]))\
            .count()
        self.assertEqual((new_mps_count - old_mps_count), 1)
        # logout before
        self.client.logout()
        # login with staff member
        self.assertEqual(
            self.client.login(
                username=self.staff.username,
                password='hostel77'),
            True)

        # publish tutorial
        pub = self.client.post(
            reverse('zds.tutorial.views.valid_tutorial'),
            {
                'tutorial': tuto.pk,
                'text': u'Ce tuto est excellent',
                'is_major': True,
                'source': 'http://zestedesavoir.com',
            },
            follow=False)

        # then active the beta on tutorial :
        sha_draft = Tutorial.objects.get(pk=tuto.pk).sha_draft
        response = self.client.post(
            reverse('zds.tutorial.views.modify_tutorial'),
            {
                'tutorial': tuto.pk,
                'activ_beta': True,
                'version': sha_draft
            },
            follow=False
        )
        self.assertEqual(302, response.status_code)
        sha_beta = Tutorial.objects.get(pk=tuto.pk).sha_beta
        self.assertEqual(sha_draft, sha_beta)

        # delete part 1
        result = self.client.post(
            reverse('zds.tutorial.views.modify_part'),
            {
                'part': p1.pk,
                'delete': "OK",
            },
            follow=True)
        # delete chapter 3
        result = self.client.post(
            reverse('zds.tutorial.views.modify_chapter'),
            {
                'chapter': c3.pk,
                'delete': "OK",
            },
            follow=True)
        self.assertEqual(Chapter.objects.filter(part__tutorial=tuto.pk).count(), 2)
        self.assertEqual(Part.objects.filter(tutorial=tuto.pk).count(), 2)

        # check view delete part and chapter (draft version)
        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_part',
                args=[
                    tuto.pk,
                    tuto.slug,
                    p1.pk,
                    p1.slug]),
            follow=True)
        self.assertEqual(result.status_code, 404)

        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_chapter',
                args=[
                    tuto.pk,
                    tuto.slug,
                    p2.pk,
                    p2.slug,
                    c3.pk,
                    c3.slug]),
            follow=True)
        self.assertEqual(result.status_code, 404)

        # deleted part and section HAVE TO be accessible on beta (get 200)
        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_part_beta',
                args=[
                    tuto.pk,
                    tuto.slug,
                    p1.pk,
                    p1.slug]),
            follow=True)
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_chapter_beta',
                args=[
                    tuto.pk,
                    tuto.slug,
                    p2.pk,
                    p2.slug,
                    c3.pk,
                    c3.slug]),
            follow=True)
        self.assertEqual(result.status_code, 200)

        # deleted part and section HAVE TO be accessible online (get 200)
        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_part_online',
                args=[
                    tuto.pk,
                    tuto.slug,
                    p1.pk,
                    p1.slug]),
            follow=True)
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_chapter_online',
                args=[
                    tuto.pk,
                    tuto.slug,
                    p2.pk,
                    p2.slug,
                    c3.pk,
                    c3.slug]),
            follow=True)
        self.assertEqual(result.status_code, 200)

        # ask public tutorial
        tuto = Tutorial.objects.get(pk=tuto.pk)
        pub = self.client.post(
            reverse('zds.tutorial.views.ask_validation'),
            {
                'tutorial': tuto.pk,
                'text': u'Ce tuto est excellent',
                'version': tuto.sha_draft,
                'source': '',
            },
            follow=False)
        self.assertEqual(pub.status_code, 302)

        # reserve tutorial
        validation = Validation.objects.filter(
            tutorial__pk=tuto.pk).last()
        pub = self.client.post(
            reverse('zds.tutorial.views.reservation', args=[validation.pk]),
            follow=False)
        self.assertEqual(pub.status_code, 302)

        # publish tutorial
        pub = self.client.post(
            reverse('zds.tutorial.views.valid_tutorial'),
            {
                'tutorial': tuto.pk,
                'text': u'Ce tuto est excellent',
                'is_major': True,
                'source': 'http://zestedesavoir.com',
            },
            follow=False)
        # check view delete part and chapter (draft version, get 404)
        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_part',
                args=[
                    tuto.pk,
                    tuto.slug,
                    p1.pk,
                    p1.slug]),
            follow=True)
        self.assertEqual(result.status_code, 404)

        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_chapter',
                args=[
                    tuto.pk,
                    tuto.slug,
                    p2.pk,
                    p2.slug,
                    c3.pk,
                    c3.slug]),
            follow=True)
        self.assertEqual(result.status_code, 404)

        # deleted part and section no longer accessible online (get 404)
        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_part_online',
                args=[
                    tuto.pk,
                    tuto.slug,
                    p1.pk,
                    p1.slug]),
            follow=True)
        self.assertEqual(result.status_code, 404)

        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_chapter_online',
                args=[
                    tuto.pk,
                    tuto.slug,
                    p2.pk,
                    p2.slug,
                    c3.pk,
                    c3.slug]),
            follow=True)
        self.assertEqual(result.status_code, 404)

        # deleted part and section still accessible on beta (get 200)
        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_part_beta',
                args=[
                    tuto.pk,
                    tuto.slug,
                    p1.pk,
                    p1.slug]),
            follow=True)
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_chapter_beta',
                args=[
                    tuto.pk,
                    tuto.slug,
                    p2.pk,
                    p2.slug,
                    c3.pk,
                    c3.slug]),
            follow=True)
        self.assertEqual(result.status_code, 200)

    def test_conflict_does_not_destroy(self):
        """tests that simultaneous edition does not conflict"""
        sub = SubCategory()
        sub.title = "toto"
        sub.save()
        # logout before
        self.client.logout()
        # first, login with author :
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)
        # test tuto
        (introduction_path,
         conclusion_path) = (os.path.join(self.bigtuto.get_path(),
                                          "introduction.md"),
                             os.path.join(self.bigtuto.get_path(),
                                          "conclusion.md"))
        hash = compute_hash([introduction_path, conclusion_path])
        self.client.post(
            reverse('zds.tutorial.views.edit_tutorial') + '?tutoriel={0}'.format(self.bigtuto.pk),
            {
                'title': self.bigtuto.title,
                'description': "nouvelle description",
                'subcategory': [sub.pk],
                'introduction': self.bigtuto.get_introduction() + " un essai",
                'conclusion': self.bigtuto.get_conclusion(),
                'licence': self.bigtuto.licence.pk,
                'last_hash': hash
            }, follow=True)
        conflict_result = self.client.post(
            reverse('zds.tutorial.views.edit_tutorial') + '?tutoriel={0}'.format(self.bigtuto.pk),
            {
                'title': self.bigtuto.title,
                'description': "nouvelle description",
                'subcategory': [sub.pk],
                'introduction': self.bigtuto.get_introduction() + " conflictual",
                'conclusion': self.bigtuto.get_conclusion(),
                'licence': self.bigtuto.licence.pk,
                'last_hash': hash
            }, follow=False)
        self.assertEqual(conflict_result.status_code, 200)
        self.assertContains(response=conflict_result, text=u"nouvelle version")

        # test parts

        self.client.post(
            reverse('zds.tutorial.views.add_part') + '?tutoriel={}'.format(self.bigtuto.pk),
            {
                'title': u"Partie 2",
                'introduction': u"Analyse",
                'conclusion': u"Fin de l'analyse",
            },
            follow=False)
        p1 = Part.objects.last()
        hash = compute_hash([os.path.join(p1.tutorial.get_path(), p1.introduction),
                             os.path.join(p1.tutorial.get_path(), p1.conclusion)])
        self.client.post(
            reverse('zds.tutorial.views.edit_part') + '?partie={}'.format(p1.pk),
            {
                'title': u"Partie 2 : edition de titre",
                'introduction': u"Expérimentation : edition d'introduction",
                'conclusion': u"C'est terminé : edition de conlusion",
                "last_hash": hash
            },
            follow=False)
        conflict_result = self.client.post(
            reverse('zds.tutorial.views.edit_part') + '?partie={}'.format(p1.pk),
            {
                'title': u"Partie 2 : edition de titre",
                'introduction': u"Expérimentation : edition d'introduction conflit",
                'conclusion': u"C'est terminé : edition de conlusion",
                "last_hash": hash
            },
            follow=False)
        self.assertEqual(conflict_result.status_code, 200)
        self.assertContains(response=conflict_result, text=u"nouvelle version")

        # test chapter
        self.client.post(
            reverse('zds.tutorial.views.add_chapter') + '?partie={}'.format(p1.pk),
            {
                'title': u"Chapitre 1",
                'introduction': "Mon premier chapitre",
                'conclusion': "Fin de mon premier chapitre",
            },
            follow=False)
        c1 = Chapter.objects.last()
        hash = compute_hash([os.path.join(c1.get_path(), "introduction.md"),
                             os.path.join(c1.get_path(), "conclusion.md")])
        self.client.post(
            reverse('zds.tutorial.views.edit_chapter') + '?chapitre={}'.format(c1.pk),
            {
                'title': u"Chapitre 3 : edition de titre",
                'introduction': u"Edition d'introduction",
                'conclusion': u"Edition de conlusion",
                "last_hash": hash
            },
            follow=True)
        conflict_result = self.client.post(
            reverse('zds.tutorial.views.edit_chapter') + '?chapitre={}'.format(c1.pk),
            {
                'title': u"Chapitre 3 : edition de titre",
                'introduction': u"Edition d'introduction conflict",
                'conclusion': u"Edition de conlusion",
                "last_hash": hash
            },
            follow=True)
        self.assertEqual(conflict_result.status_code, 200)
        self.assertContains(response=conflict_result, text=u"nouvelle version")

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
                    self.part2.pk,
                    self.part2.slug]),
            follow=True)
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse('zds.tutorial.views.view_chapter_online',
                    args=[self.bigtuto.pk,
                          self.bigtuto.slug,
                          self.part2.pk,
                          self.part2.slug,
                          self.chapter2_1.pk,
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
                    self.part2.pk,
                    self.part2.slug]),
            follow=True)
        self.assertEqual(result.status_code, 403)

        result = self.client.get(
            reverse('zds.tutorial.views.view_chapter',
                    args=[self.bigtuto.pk,
                          self.bigtuto.slug,
                          self.part2.pk,
                          self.part2.slug,
                          self.chapter2_1.pk,
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
                    self.part2.pk,
                    self.part2.slug]),
            follow=True)
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse('zds.tutorial.views.view_chapter_online',
                    args=[self.bigtuto.pk,
                          self.bigtuto.slug,
                          self.part2.pk,
                          self.part2.slug,
                          self.chapter2_1.pk,
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
                    self.part2.pk,
                    self.part2.slug]),
            follow=True)
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse('zds.tutorial.views.view_chapter',
                    args=[self.bigtuto.pk,
                          self.bigtuto.slug,
                          self.part2.pk,
                          self.part2.slug,
                          self.chapter2_1.pk,
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
                    self.part2.pk,
                    self.part2.slug]),
            follow=True)
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse('zds.tutorial.views.view_chapter_online',
                    args=[self.bigtuto.pk,
                          self.bigtuto.slug,
                          self.part2.pk,
                          self.part2.slug,
                          self.chapter2_1.pk,
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
                    self.part2.pk,
                    self.part2.slug]),
            follow=True)
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse('zds.tutorial.views.view_chapter',
                    args=[self.bigtuto.pk,
                          self.bigtuto.slug,
                          self.part2.pk,
                          self.part2.slug,
                          self.chapter2_1.pk,
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

    def test_add_remove_authors(self):
        user1 = ProfileFactory().user

        # Add and remove author as simple user (not staff):
        login_check = self.client.login(
            username=self.user.username,
            password='hostel77')
        self.assertEqual(login_check, True)

        result = self.client.post(
            reverse('zds.tutorial.views.modify_tutorial'),
            {
                'author': user1.username,
                'tutorial': self.bigtuto.pk,
                'add_author': True,
            },
            follow=False)
        self.assertEqual(result.status_code, 403)

        result = self.client.post(
            reverse('zds.tutorial.views.modify_tutorial'),
            {
                'author': user1.pk,
                'tutorial': self.bigtuto.pk,
                'remove_author': True,
            },
            follow=False)
        self.assertEqual(result.status_code, 403)

        # Add and remove author as staff:
        login_check = self.client.login(
            username=self.staff.username,
            password='hostel77')
        self.assertEqual(login_check, True)

        result = self.client.post(
            reverse('zds.tutorial.views.modify_tutorial'),
            {
                'author': user1.username,
                'tutorial': self.bigtuto.pk,
                'add_author': True,
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        result = self.client.post(
            reverse('zds.tutorial.views.modify_tutorial'),
            {
                'author': user1.pk,
                'tutorial': self.bigtuto.pk,
                'remove_author': True,
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

    def test_delete_image_tutorial(self):
        """To test delete image of a tutorial."""
        # Author of the tutorial and the gallery (read and write permissions).
        login_check = self.client.login(username=self.user_author.username, password='hostel77')
        self.assertTrue(login_check)

        # Attach an image of a gallery at a tutorial.
        image_tutorial = ImageFactory(gallery=self.bigtuto.gallery)
        UserGalleryFactory(user=self.user_author, gallery=self.bigtuto.gallery)

        self.bigtuto.image = image_tutorial
        self.bigtuto.save()

        self.assertTrue(Tutorial.objects.get(pk=self.bigtuto.pk).image is not None)

        # Delete the image of the bigtuto.

        response = self.client.post(
            reverse('gallery-image-delete'),
            {
                'gallery': self.bigtuto.gallery.pk,
                'delete_multi': '',
                'items': [image_tutorial.pk]
            },
            follow=True
        )
        self.assertEqual(200, response.status_code)

        # Check if the tutorial is already in database and it doesn't have image.
        self.assertEqual(1, Tutorial.objects.filter(pk=self.bigtuto.pk).count())
        self.assertTrue(Tutorial.objects.get(pk=self.bigtuto.pk).image is None)

    def test_workflow_beta_tuto(self):
        "Ensure the behavior of the beta version of tutorials"
        ForumFactory(
            category=CategoryFactory(position=1),
            position_in_category=1)
        # logout before
        self.client.logout()

        # check if acess to page with beta tutorial (with guest)
        response = self.client.get(
            reverse(
                'zds.tutorial.views.find_tuto',
                args=[self.user_author.pk]
            ) + '?type=beta'
        )
        self.assertEqual(200, response.status_code)

        # then, login with author :
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)

        # check if acess to page with beta tutorial (with author)
        response = self.client.get(
            reverse(
                'zds.tutorial.views.find_tuto',
                args=[self.user_author.pk]
            ) + '?type=beta'
        )
        self.assertEqual(200, response.status_code)

        # then active the beta on tutorial :
        sha_draft = Tutorial.objects.get(pk=self.bigtuto.pk).sha_draft
        response = self.client.post(
            reverse('zds.tutorial.views.modify_tutorial'),
            {
                'tutorial': self.bigtuto.pk,
                'activ_beta': True,
                'version': sha_draft
            },
            follow=False
        )
        self.assertEqual(302, response.status_code)

        # check if acess to page with beta tutorial (with author)
        response = self.client.get(
            reverse(
                'zds.tutorial.views.find_tuto',
                args=[self.user_author.pk]
            ) + '?type=beta'
        )
        self.assertEqual(200, response.status_code)
        # test beta :
        self.assertEqual(
            Tutorial.objects.get(pk=self.bigtuto.pk).sha_beta,
            sha_draft)
        url = Tutorial.objects.get(pk=self.bigtuto.pk).get_absolute_url_beta()
        sha_beta = sha_draft
        # Test access for author (get 200)
        self.assertEqual(
            self.client.get(url).status_code,
            200)
        # test access from outside (get 302, connexion form)
        self.client.logout()
        self.assertEqual(
            self.client.get(url).status_code,
            302)
        # check if acess to page with beta tutorial (with guest, get 200)
        response = self.client.get(
            reverse(
                'zds.tutorial.views.find_tuto',
                args=[self.user_author.pk]
            ) + '?type=beta'
        )
        self.assertEqual(200, response.status_code)
        # test tutorial acess for random user
        self.assertEqual(
            self.client.login(
                username=self.user.username,
                password='hostel77'),
            True)
        # check if acess to page with beta tutorial (with random user, get 200)
        response = self.client.get(
            reverse(
                'zds.tutorial.views.find_tuto',
                args=[self.user_author.pk]
            ) + '?type=beta'
        )
        # test access (get 200)
        self.assertEqual(
            self.client.get(url).status_code,
            200)

        # then modify tutorial
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)
        result = self.client.post(
            reverse('zds.tutorial.views.add_extract') +
            '?chapitre={0}'.format(
                self.chapter2_1.pk),

            {
                'title': "Introduction",
                'text': u"Le contenu de l'extrait"
            })

        self.assertEqual(result.status_code, 302)
        self.assertEqual(
            Tutorial.objects.get(pk=self.bigtuto.pk).sha_beta,
            sha_beta)
        self.assertNotEqual(
            Tutorial.objects.get(pk=self.bigtuto.pk).sha_draft,
            sha_beta)
        # update beta
        sha_draft = Tutorial.objects.get(pk=self.bigtuto.pk).sha_draft
        response = self.client.post(
            reverse('zds.tutorial.views.modify_tutorial'),
            {
                'tutorial': self.bigtuto.pk,
                'update_beta': True,
                'version': sha_draft
            },
            follow=False
        )
        self.assertEqual(302, response.status_code)
        url = Tutorial.objects.get(pk=self.bigtuto.pk).get_absolute_url_beta()
        # test access to new beta url (get 200) :
        self.assertEqual(
            self.client.get(url).status_code,
            200)
        # test access for random user to new url (get 200) and old (get 403)
        self.assertEqual(
            self.client.login(
                username=self.user.username,
                password='hostel77'),
            True)
        self.assertEqual(
            self.client.get(url).status_code,
            200)

        # then desactive beta :
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)
        response = self.client.post(
            reverse('zds.tutorial.views.modify_tutorial'),
            {
                'tutorial': self.bigtuto.pk,
                'desactiv_beta': True,
                'version': sha_draft
            },
            follow=False
        )
        self.assertEqual(302, response.status_code)
        self.assertEqual(
            Tutorial.objects.get(pk=self.bigtuto.pk).sha_beta,
            None)
        # test access from outside (get 302, connexion form)
        self.client.logout()
        self.assertEqual(
            self.client.get(url).status_code,
            302)
        # test access for random user (get 403)
        self.assertEqual(
            self.client.login(
                username=self.user.username,
                password='hostel77'),
            True)
        self.assertEqual(
            self.client.get(url).status_code,
            403)

        # ensure staff behavior (staff can also active/update/desactive beta)
        self.assertEqual(
            self.client.login(
                username=self.staff.username,
                password='hostel77'),
            True)
        response = self.client.post(
            reverse('zds.tutorial.views.modify_tutorial'),
            {
                'tutorial': self.bigtuto.pk,
                'activ_beta': True,
                'version': sha_draft
            },
            follow=False
        )
        self.assertEqual(302, response.status_code)
        # test access from outside (get 302, connexion form)
        self.client.logout()
        self.assertEqual(
            self.client.get(url).status_code,
            302)
        # test access for random user (get 200)
        self.assertEqual(
            self.client.login(
                username=self.user.username,
                password='hostel77'),
            True)
        self.assertEqual(
            self.client.get(url).status_code,
            200)

    def test_gallery_tuto_change_name(self):
        """
        Test if the gallery attached to a tutorial change its name when the tuto
        has the name changed.
        """

        newtitle = u"The New Title"
        self.client.post(
            reverse('zds.tutorial.views.edit_tutorial') + '?tutoriel={}'.format(self.bigtuto.pk),
            {
                'title': newtitle,
                'subcategory': self.subcat.pk,
                'introduction': self.bigtuto.introduction,
                'description': self.bigtuto.description,
                'conclusion': self.bigtuto.conclusion,
                'licence': self.bigtuto.licence.pk,
                'last_hash': compute_hash([os.path.join(self.bigtuto.get_path(), "introduction.md"),
                                           os.path.join(self.bigtuto.get_path(), "conclusion.md")])
            },
            follow=True)

        tuto = Tutorial.objects.filter(pk=self.bigtuto.pk).first()
        self.assertEqual(tuto.title, newtitle)
        self.assertEqual(tuto.gallery.title, tuto.title)
        self.assertEqual(tuto.gallery.slug, tuto.slug)

    def test_workflow_licence(self):
        '''Ensure the behavior of licence on mini-tutorials'''

        # create a new licence
        new_licence = LicenceFactory(code='CC_BY', title='Creative Commons BY')
        new_licence = Licence.objects.get(pk=new_licence.pk)

        # check value first
        tuto = Tutorial.objects.get(pk=self.bigtuto.pk)
        self.assertEqual(tuto.licence.pk, self.licence.pk)

        # get value wich does not change (speed up test)
        introduction = self.bigtuto.get_introduction()
        conclusion = self.bigtuto.get_conclusion()
        hash = compute_hash([
            os.path.join(self.bigtuto.get_path(), "introduction.md"),
            os.path.join(self.bigtuto.get_path(), "conclusion.md")
        ])

        # logout before
        self.client.logout()
        # login with author
        self.assertTrue(
            self.client.login(
                username=self.user_author.username,
                password='hostel77')
        )

        # change licence (get 302) :
        result = self.client.post(
            reverse('zds.tutorial.views.edit_tutorial') +
            '?tutoriel={}'.format(self.bigtuto.pk),
            {
                'title': self.bigtuto.title,
                'description': self.bigtuto.description,
                'introduction': introduction,
                'conclusion': conclusion,
                'subcategory': self.subcat.pk,
                'licence': new_licence.pk,
                'last_hash': hash
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        # test change :
        tuto = Tutorial.objects.get(pk=self.bigtuto.pk)
        self.assertNotEqual(tuto.licence.pk, self.licence.pk)
        self.assertEqual(tuto.licence.pk, new_licence.pk)

        # test change in JSON :
        json = tuto.load_json()
        self.assertEquals(json['licence'], new_licence.code)

        # then logout ...
        self.client.logout()
        # ... and login with staff
        self.assertTrue(
            self.client.login(
                username=self.staff.username,
                password='hostel77')
        )

        # change licence back to old one (get 302, staff can change licence) :
        result = self.client.post(
            reverse('zds.tutorial.views.edit_tutorial') +
            '?tutoriel={}'.format(self.bigtuto.pk),
            {
                'title': self.bigtuto.title,
                'description': self.bigtuto.description,
                'introduction': introduction,
                'conclusion': conclusion,
                'subcategory': self.subcat.pk,
                'licence': self.licence.pk,
                'last_hash': hash
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        # test change :
        tuto = Tutorial.objects.get(pk=self.bigtuto.pk)
        self.assertEqual(tuto.licence.pk, self.licence.pk)
        self.assertNotEqual(tuto.licence.pk, new_licence.pk)

        # test change in JSON :
        json = tuto.load_json()
        self.assertEquals(json['licence'], self.licence.code)

        # then logout ...
        self.client.logout()

        # change licence (get 302, redirection to login page) :
        result = self.client.post(
            reverse('zds.tutorial.views.edit_tutorial') +
            '?tutoriel={}'.format(self.bigtuto.pk),
            {
                'title': self.bigtuto.title,
                'description': self.bigtuto.description,
                'introduction': introduction,
                'conclusion': conclusion,
                'subcategory': self.subcat.pk,
                'licence': new_licence.pk,
                'last_hash': hash
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        # test change (normaly, nothing has) :
        tuto = Tutorial.objects.get(pk=self.bigtuto.pk)
        self.assertEqual(tuto.licence.pk, self.licence.pk)
        self.assertNotEqual(tuto.licence.pk, new_licence.pk)

        # login with random user
        self.assertTrue(
            self.client.login(
                username=self.user.username,
                password='hostel77')
        )

        # change licence (get 403, random user cannot edit bigtuto if not in
        # authors list) :
        result = self.client.post(
            reverse('zds.tutorial.views.edit_tutorial') +
            '?tutoriel={}'.format(self.bigtuto.pk),
            {
                'title': self.bigtuto.title,
                'description': self.bigtuto.description,
                'introduction': introduction,
                'conclusion': conclusion,
                'subcategory': self.subcat.pk,
                'licence': new_licence.pk,
                'last_hash': hash
            },
            follow=False)
        self.assertEqual(result.status_code, 403)

        # test change (normaly, nothing has) :
        tuto = Tutorial.objects.get(pk=self.bigtuto.pk)
        self.assertEqual(tuto.licence.pk, self.licence.pk)
        self.assertNotEqual(tuto.licence.pk, new_licence.pk)

        # test change in JSON (normaly, nothing has) :
        json = tuto.load_json()
        self.assertEquals(json['licence'], self.licence.code)

    def test_workflow_archive_tuto(self):
        """ensure the behavior of archive with a big tutorial"""

        # login with author
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)

        # modify tutorial, add a new extract (NOTE: zipfile does not ensure UTF-8):
        extract_content = u'Le contenu de l\'extrait'
        extract_title = u'Un titre d\'extrait'
        result = self.client.post(
            reverse('zds.tutorial.views.add_extract') +
            '?chapitre={0}'.format(
                self.chapter2_1.pk),
            {
                'title': extract_title,
                'text': extract_content
            })
        self.assertEqual(result.status_code, 302)

        # now, draft and public version are not the same
        tutorial = Tutorial.objects.get(pk=self.bigtuto.pk)
        self.assertNotEqual(tutorial.sha_draft, tutorial.sha_public)
        # store extract
        added_extract = Extract.objects.get(chapter=Chapter.objects.get(pk=self.chapter2_1.pk))

        # fetch archives :
        # 1. draft version
        result = self.client.get(
            reverse('zds.tutorial.views.download') +
            '?tutoriel={0}'.format(
                self.bigtuto.pk),
            follow=False)
        self.assertEqual(result.status_code, 200)
        draft_zip_path = os.path.join(tempfile.gettempdir(), '__draft.zip')
        f = open(draft_zip_path, 'w')
        f.write(result.content)
        f.close()
        # 2. online version :
        result = self.client.get(
            reverse('zds.tutorial.views.download') +
            '?tutoriel={0}&online'.format(
                self.bigtuto.pk),
            follow=False)
        self.assertEqual(result.status_code, 200)
        online_zip_path = os.path.join(tempfile.gettempdir(), '__online.zip')
        f = open(online_zip_path, 'w')
        f.write(result.content)
        f.close()

        # note : path is "/2_ma-partie-no2/4_mon-chapitre-no4/"
        # now check if modification are in draft version of archive and not in the public one
        draft_zip = zipfile.ZipFile(draft_zip_path, 'r')
        online_zip = zipfile.ZipFile(online_zip_path, 'r')

        # first, test in manifest
        online_manifest = json_reader.loads(online_zip.read('manifest.json'))
        found = False
        for part in online_manifest['parts']:
            if part['pk'] == self.part2.pk:
                for chapter in part['chapters']:
                    if chapter['pk'] == self.chapter2_1.pk:
                        for extract in chapter['extracts']:
                            if extract['pk'] == added_extract.pk:
                                found = True
        self.assertFalse(found)  # extract cannot exists in the online version

        draft_manifest = json_reader.loads(draft_zip.read('manifest.json'))
        extract_in_manifest = []
        for part in draft_manifest['parts']:
            if part['pk'] == self.part2.pk:
                for chapter in part['chapters']:
                    if chapter['pk'] == self.chapter2_1.pk:
                        for extract in chapter['extracts']:
                            if extract['pk'] == added_extract.pk:
                                found = True
                                extract_in_manifest = extract
        self.assertTrue(found)  # extract exists in draft version
        self.assertEqual(extract_in_manifest['title'], extract_title)

        # and then, test the file directly :
        found = True
        try:
            online_zip.getinfo(extract_in_manifest['text'])
        except KeyError:
            found = False
        self.assertFalse(found)  # extract cannot exists in the online version

        found = True
        try:
            draft_zip.getinfo(extract_in_manifest['text'])
        except KeyError:
            found = False
        self.assertTrue(found)  # extract exists in the draft one
        self.assertEqual(draft_zip.read(extract_in_manifest['text']), extract_content)  # content is good

        draft_zip.close()
        online_zip.close()

        # then logout and test access
        self.client.logout()

        # public cannot access to draft version of tutorial
        result = self.client.get(
            reverse('zds.tutorial.views.download') +
            '?tutoriel={0}'.format(
                self.bigtuto.pk),
            follow=False)
        self.assertEqual(result.status_code, 403)
        # ... but can access to online version
        result = self.client.get(
            reverse('zds.tutorial.views.download') +
            '?tutoriel={0}&online'.format(
                self.bigtuto.pk),
            follow=False)
        self.assertEqual(result.status_code, 200)

        # login with random user
        self.assertEqual(
            self.client.login(
                username=self.user.username,
                password='hostel77'),
            True)

        # cannot access to draft version of tutorial (if not author or staff)
        result = self.client.get(
            reverse('zds.tutorial.views.download') +
            '?tutoriel={0}'.format(
                self.bigtuto.pk),
            follow=False)
        self.assertEqual(result.status_code, 403)
        # but can access to online one
        result = self.client.get(
            reverse('zds.tutorial.views.download') +
            '?tutoriel={0}&online'.format(
                self.bigtuto.pk),
            follow=False)
        self.assertEqual(result.status_code, 200)
        self.client.logout()

        # login with staff user
        self.assertEqual(
            self.client.login(
                username=self.staff.username,
                password='hostel77'),
            True)

        # staff can access to draft version of tutorial
        result = self.client.get(
            reverse('zds.tutorial.views.download') +
            '?tutoriel={0}'.format(
                self.bigtuto.pk),
            follow=False)
        self.assertEqual(result.status_code, 200)
        # ... and also to online version
        result = self.client.get(
            reverse('zds.tutorial.views.download') +
            '?tutoriel={0}&online'.format(
                self.bigtuto.pk),
            follow=False)
        self.assertEqual(result.status_code, 200)

        # finally, clean up things:
        os.remove(draft_zip_path)
        os.remove(online_zip_path)

    def test_change_update(self):
        """test the change of `tutorial.update` if part/chapter/extract are modified (ensure #1715) """

        # login with author
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)

        time_0 = datetime.datetime.fromtimestamp(0)  # way deep in the past
        tutorial = Tutorial.objects.get(pk=self.bigtuto.pk)
        tutorial.update = time_0
        tutorial.save()

        # first, ensure the modification
        tutorial = Tutorial.objects.get(pk=self.bigtuto.pk)
        self.assertEqual(tutorial.update, time_0)

        # add part (implicit call to `maj_repo_part()`)
        result = self.client.post(
            reverse('zds.tutorial.views.add_part') + '?tutoriel={}'.format(tutorial.pk),
            {
                'title': u"Une nouvelle partie",
                'introduction': "Expérimentation",
                'conclusion': "C'est terminé",
                'msg_commit': u"Nouvelle partie"
            },
            follow=False)

        tutorial = Tutorial.objects.get(pk=self.bigtuto.pk)
        self.assertNotEqual(tutorial.update, time_0)
        tutorial.update = time_0
        tutorial.save()

        # edit part (implicit call to `maj_repo_part()`)
        part = Part.objects.filter(tutorial=tutorial).last()
        result = self.client.post(
            reverse('zds.tutorial.views.edit_part') + '?partie={}'.format(part.pk),
            {
                'title': u"Cette partie a changé de nom",
                'introduction': u"Expérimentation : edition d'introduction",
                'conclusion': u"C'est terminé : edition de conlusion",
                'msg_commit': u"Changement de la partie",
                "last_hash": compute_hash([os.path.join(part.tutorial.get_path(), part.introduction),
                                           os.path.join(part.tutorial.get_path(), part.conclusion)])
            },
            follow=True)
        self.assertEqual(result.status_code, 200)

        tutorial = Tutorial.objects.get(pk=self.bigtuto.pk)
        self.assertNotEqual(tutorial.update, time_0)
        tutorial.update = time_0
        tutorial.save()

        # add chapter  (implicit call to `maj_repo_chapter()`)
        result = self.client.post(
            reverse('zds.tutorial.views.add_chapter') + '?partie={}'.format(part.pk),
            {
                'title': u"Cuisine des agrumes sur ZdS",
                'introduction': "Mon premier chapitre",
                'conclusion': "Fin de mon premier chapitre",
                'msg_commit': u"Initialisation du chapitre 1"
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        tutorial = Tutorial.objects.get(pk=self.bigtuto.pk)
        self.assertNotEqual(tutorial.update, time_0)
        tutorial.update = time_0
        tutorial.save()

        # edit chapter (implicit call to `maj_repo_chapter()`)
        chapter = Chapter.objects.filter(part=part).last()
        result = self.client.post(
            reverse('zds.tutorial.views.edit_chapter') + '?chapitre={}'.format(chapter.pk),
            {
                'title': u"Le respect des agrumes sur ZdS",
                'introduction': u"Edition d'introduction",
                'conclusion': u"Edition de conlusion",
                'msg_commit': u"MàJ du chapitre 2 : le respect des agrumes sur ZdS",
                "last_hash": compute_hash([
                    os.path.join(chapter.get_path(), "introduction.md"),
                    os.path.join(chapter.get_path(), "conclusion.md")])
            },
            follow=True)
        self.assertEqual(result.status_code, 200)

        tutorial = Tutorial.objects.get(pk=self.bigtuto.pk)
        self.assertNotEqual(tutorial.update, time_0)
        tutorial.update = time_0
        tutorial.save()

        # add another extract (implicit call to `maj_repo_extract()`)
        result = self.client.post(
            reverse('zds.tutorial.views.add_extract') + '?chapitre={0}'.format(chapter.pk),
            {
                'title': u'Un second extrait',
                'text': u'Comment extraire le jus des agrumes ? Est-ce torturer Clem ?'
            })
        self.assertEqual(result.status_code, 302)

        tutorial = Tutorial.objects.get(pk=self.bigtuto.pk)
        self.assertNotEqual(tutorial.update, time_0)
        tutorial.update = time_0
        tutorial.save()

        # edit extract (implicit call to `maj_repo_extract()`)
        extract = chapter.get_extracts()[0]
        result = self.client.post(
            reverse('zds.tutorial.views.edit_extract') + '?extrait={}'.format(extract.pk),
            {
                'title': u"Extrait 2 : edition de titre",
                'text': u"On ne torture pas les agrumes !",
                "last_hash": compute_hash([os.path.join(extract.get_path())])
            },
            follow=True)
        self.assertEqual(result.status_code, 200)
        self.assertNotEqual(Tutorial.objects.get(pk=self.bigtuto.pk), time_0)

    def test_warn_typo(self):
        """
        Add a non-regression test about warning the author(s) of a typo in tutorial
        """

        bot = Group(name=settings.ZDS_APP["member"]["bot_group"])
        bot.save()

        typo_text = u'T\'as fait une faute, t\'es nul'

        # login with author
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)

        # check if author get error when warning typo on its own tutorial
        result = self.client.post(
            reverse('zds.tutorial.views.warn_typo', args=[u"tutorial", self.bigtuto.pk]),
            {
                'explication': u'ceci est un test',
                'version_tutorial': self.bigtuto.sha_public
            },
            follow=True)
        self.assertEqual(result.status_code, 200)

        msgs = result.context['messages']
        last = None
        for msg in msgs:
            last = msg
        self.assertEqual(last.level, messages.ERROR)

        # login with normal user
        self.client.logout()

        self.assertEqual(
            self.client.login(
                username=self.user.username,
                password='hostel77'),
            True)

        # check if user can warn typo in tutorial
        result = self.client.post(
            reverse('zds.tutorial.views.warn_typo', args=[u"tutorial", self.bigtuto.pk]),
            {
                'explication': typo_text,
                'version_tutorial': self.bigtuto.sha_public
            },
            follow=True)
        self.assertEqual(result.status_code, 200)

        msgs = result.context['messages']
        last = None
        for msg in msgs:
            last = msg
        self.assertEqual(last.level, messages.SUCCESS)

        # check PM :
        sent_pm = PrivateTopic.objects.filter(author=self.user.pk).last()
        self.assertIn(self.user_author, sent_pm.participants.all())  # author is in participants
        self.assertIn(typo_text, sent_pm.last_message.text)  # typo is in message
        self.assertIn(self.bigtuto.get_absolute_url_online(), sent_pm.last_message.text)  # public url is in message

        # check if user can warn typo in chapter of tutorial
        result = self.client.post(
            reverse('zds.tutorial.views.warn_typo', args=[u"chapter", self.chapter1_1.pk]),
            {
                'explication': typo_text,
                'version_tutorial': self.bigtuto.sha_public
            },
            follow=True)
        self.assertEqual(result.status_code, 200)

        msgs = result.context['messages']
        last = None
        for msg in msgs:
            last = msg
        self.assertEqual(last.level, messages.SUCCESS)

        # check PM :
        sent_pm = PrivateTopic.objects.filter(author=self.user.pk).last()
        self.assertIn(self.user_author, sent_pm.participants.all())  # author is in participants
        self.assertIn(typo_text, sent_pm.last_message.text)  # typo is in message
        self.assertIn(self.chapter1_1.get_absolute_url_online(), sent_pm.last_message.text)  # public url is in message

        # induce a change and put in beta :
        self.client.logout()

        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)

        result = self.client.post(
            reverse('zds.tutorial.views.add_extract') + '?chapitre={0}'.format(self.chapter1_1.pk),
            {
                'title': u'Un nouveau titre d\'extrait',
                'text': u'I do not fear computers. I fear the lack of them. (I. Asimov)'
            })
        self.assertEqual(result.status_code, 302)

        sha_draft = Tutorial.objects.get(pk=self.bigtuto.pk).sha_draft
        response = self.client.post(
            reverse('zds.tutorial.views.modify_tutorial'),
            {
                'tutorial': self.bigtuto.pk,
                'activ_beta': True,
                'version': sha_draft
            },
            follow=False
        )
        self.assertEqual(302, response.status_code)

        # login with normal user
        self.client.logout()

        self.assertEqual(
            self.client.login(
                username=self.user.username,
                password='hostel77'),
            True)

        # check if user can warn typo in tutorial in beta version
        sha_beta = Tutorial.objects.get(pk=self.bigtuto.pk).sha_beta
        result = self.client.post(
            reverse('zds.tutorial.views.warn_typo', args=[u"tutorial", self.bigtuto.pk]),
            {
                'explication': typo_text,
                'version_tutorial': sha_beta
            },
            follow=True)
        self.assertEqual(result.status_code, 200)

        msgs = result.context['messages']
        last = None
        for msg in msgs:
            last = msg
        self.assertEqual(last.level, messages.SUCCESS)

        # check PM :
        sent_pm = PrivateTopic.objects.filter(author=self.user.pk).last()
        self.assertIn(self.user_author, sent_pm.participants.all())  # author is in participants
        self.assertIn(typo_text, sent_pm.last_message.text)  # typo is in message
        self.assertIn(Tutorial.objects.get(pk=self.bigtuto.pk).get_absolute_url_beta(),
                      sent_pm.last_message.text)  # beta url is in message !

        # check if user can warn typo in chapter of tutorial
        result = self.client.post(
            reverse('zds.tutorial.views.warn_typo', args=[u"chapter", self.chapter1_1.pk]),
            {
                'explication': typo_text,
                'version_tutorial': sha_beta
            },
            follow=True)
        self.assertEqual(result.status_code, 200)

        msgs = result.context['messages']
        last = None
        for msg in msgs:
            last = msg
        self.assertEqual(last.level, messages.SUCCESS)

        # check PM :
        sent_pm = PrivateTopic.objects.filter(author=self.user.pk).last()
        self.assertIn(self.user_author, sent_pm.participants.all())  # author is in participants
        self.assertIn(typo_text, sent_pm.last_message.text)  # typo is in message
        self.assertIn(Chapter.objects.get(pk=self.chapter1_1.pk).get_absolute_url_beta(),
                      sent_pm.last_message.text)  # public url is in message

    def test_get_published_content(self):
        """
        Add a non-regression test for not indexing content that have not been published.
        """

        count_parts = len(self.bigtuto.get_parts())
        count_chapter = Chapter.objects.count()

        # Non published Chapter and Extracts
        non_published_chapter_link_tuto = ChapterFactory(tutorial=self.bigtuto)
        ExtractFactory(chapter=non_published_chapter_link_tuto, position_in_chapter=1)

        # Non published parts, chapters and extracts
        self.part4 = PartFactory(tutorial=self.bigtuto, position_in_tutorial=4)
        non_published_chapter = ChapterFactory(part=self.part4)
        ExtractFactory(chapter=non_published_chapter, position_in_chapter=1)

        # Create a non published parts and chapters
        self.part5 = PartFactory(tutorial=self.bigtuto, position_in_tutorial=5)
        ChapterFactory(part=self.part5)

        # Empty non published parts
        PartFactory(tutorial=self.bigtuto, position_in_tutorial=6)

        # Empty non published chapters
        ChapterFactory(tutorial=self.bigtuto)

        published_content = GetPublished().get_published_content()
        self.assertEqual(len(published_content["parts"]), count_parts)
        self.assertEqual(len(published_content["chapters"]), count_chapter)

        # Clear all the lists
        GetPublished.published_part = []
        GetPublished.published_chapter = []
        GetPublished.published_extract = []

        # Manifest for tutorial with parts only
        m = '{"title": "Ceci est un test", "parts": [{"pk": 1}] }'
        json = json_reader.loads(m)

        GetPublished.load_tutorial(json)
        self.assertEqual(GetPublished.published_part[0], 1)

        GetPublished.published_part = []

        # Manifest for tutorial with chapters only
        m = '{"title": "Ceci est un test", "chapters": [{"pk": 1}] }'
        json = json_reader.loads(m)

        GetPublished.load_tutorial(json)
        self.assertEqual(GetPublished.published_chapter[0], 1)

        GetPublished.published_chapter = []

        # Manifest for tutorial with extracts only
        m = '{"title": "Ceci est un test", "extracts": [{"pk": 1}] }'
        json = json_reader.loads(m)

        GetPublished.load_tutorial(json)
        self.assertEqual(GetPublished.published_extract[0], 1)

        GetPublished.published_extract = []

        # Manifest for tutorial with parts, chapters and extracts
        m = '{"title": "Ceci est un test", "parts": [{"pk": 1, "chapters":[{"pk": 2, "extracts":[{"pk": 3}] }] }] }'
        json = json_reader.loads(m)

        GetPublished.load_tutorial(json)
        self.assertEqual(GetPublished.published_part[0], 1)
        self.assertEqual(GetPublished.published_chapter[0], 2)
        self.assertEqual(GetPublished.published_extract[0], 3)

        # Manifest for tutorial with chapters and extracts
        GetPublished.published_part = []
        GetPublished.published_chapter = []
        GetPublished.published_extract = []

        m = '{"title": "Ceci est un test", "chapters": [{"pk": 1, "extracts":[{"pk": 2}] }] }'
        json = json_reader.loads(m)

        GetPublished.load_tutorial(json)
        self.assertEqual(GetPublished.published_chapter[0], 1)
        self.assertEqual(GetPublished.published_extract[0], 2)

        GetPublished.published_chapter = []
        GetPublished.published_extract = []

        # Manifest for tutorial with parts and chapters

        m = '{"title": "Ceci est un test", "parts": [{"pk": 1, "chapters":[{"pk": 2}] }] }'
        json = json_reader.loads(m)

        GetPublished.load_tutorial(json)
        self.assertEqual(GetPublished.published_part[0], 1)
        self.assertEqual(GetPublished.published_chapter[0], 2)

        GetPublished.published_part = []
        GetPublished.published_chapter = []

    def tearDown(self):
        if os.path.isdir(settings.ZDS_APP['tutorial']['repo_path']):
            shutil.rmtree(settings.ZDS_APP['tutorial']['repo_path'])
        if os.path.isdir(settings.ZDS_APP['tutorial']['repo_public_path']):
            shutil.rmtree(settings.ZDS_APP['tutorial']['repo_public_path'])
        if os.path.isdir(settings.ZDS_APP['article']['repo_path']):
            shutil.rmtree(settings.ZDS_APP['article']['repo_path'])
        if os.path.isdir(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)


@override_settings(MEDIA_ROOT=os.path.join(BASE_DIR, 'media-test'))
@override_settings(ZDS_APP=overrided_zds_app)
class MiniTutorialTests(TestCase):

    def setUp(self):

        settings.EMAIL_BACKEND = \
            'django.core.mail.backends.locmem.EmailBackend'
        self.mas = ProfileFactory().user
        settings.ZDS_APP['member']['bot_account'] = self.mas.username

        self.user_author = ProfileFactory().user
        self.user = ProfileFactory().user
        self.staff = StaffProfileFactory().user

        self.subcat = SubCategoryFactory()

        ForumFactory(
            pk=settings.ZDS_APP['forum']['beta_forum_id'],
            category=CategoryFactory(position=1),
            position_in_category=1)

        self.licence = LicenceFactory()
        self.licence.save()

        self.minituto = MiniTutorialFactory(light=True)
        self.minituto.authors.add(self.user_author)
        self.minituto.gallery = GalleryFactory()
        self.minituto.licence = self.licence
        self.minituto.save()

        self.chapter = ChapterFactory(
            tutorial=self.minituto,
            position_in_tutorial=1,
            light=True)

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
                'version': self.minituto.sha_draft,
                'source': 'http://zestedesavoir.com',
            },
            follow=False)
        self.assertEqual(pub.status_code, 302)

        # reserve tutorial
        validation = Validation.objects.get(
            tutorial__pk=self.minituto.pk)
        pub = self.client.post(
            reverse('zds.tutorial.views.reservation', args=[validation.pk]),
            follow=False)
        self.assertEqual(pub.status_code, 302)

        # publish tutorial
        pub = self.client.post(
            reverse('zds.tutorial.views.valid_tutorial'),
            {
                'tutorial': self.minituto.pk,
                'text': u'Ce tuto est excellent',
                'is_major': True,
                'source': 'http://zestedesavoir.com',
            },
            follow=False)
        self.assertEqual(pub.status_code, 302)
        self.minituto = Tutorial.objects.get(pk=self.minituto.pk)
        self.assertEqual(self.minituto.on_line(), True)
        self.assertEquals(len(mail.outbox), 1)

        mail.outbox = []

    def test_import_archive(self):
        login_check = self.client.login(
            username=self.user_author.username,
            password='hostel77')
        self.assertEqual(login_check, True)
        # create temporary data directory
        temp = os.path.join(tempfile.gettempdir(), "temp")
        if not os.path.exists(temp):
            os.makedirs(temp, mode=0777)
        # download zip
        repo_path = os.path.join(settings.ZDS_APP['tutorial']['repo_path'], self.minituto.get_phy_slug())
        repo = Repo(repo_path)
        zip_path = os.path.join(tempfile.gettempdir(), self.minituto.slug + '.zip')
        zip_file = zipfile.ZipFile(zip_path, 'w')
        insert_into_zip(zip_file, repo.commit(self.minituto.sha_draft).tree)
        zip_file.close()

        zip_dir = os.path.join(temp, self.minituto.get_phy_slug())
        if not os.path.exists(zip_dir):
            os.makedirs(zip_dir, mode=0777)

        # Extract zip
        with zipfile.ZipFile(zip_path) as zip_file:
            for member in zip_file.namelist():
                filename = os.path.basename(member)
                # skip directories
                if not filename:
                    continue
                if not os.path.exists(os.path.dirname(os.path.join(zip_dir, member))):
                    os.makedirs(os.path.dirname(os.path.join(zip_dir, member)), mode=0777)
                # copy file (taken from zipfile's extract)
                source = zip_file.open(member)
                target = file(os.path.join(zip_dir, filename), "wb")
                with source, target:
                    shutil.copyfileobj(source, target)
        self.assertTrue(os.path.isdir(zip_dir))

        # update markdown files
        up_intro_tfile = open(os.path.join(temp, self.minituto.get_phy_slug(), self.minituto.introduction), "a")
        up_intro_tfile.write(u"preuve de modification de l'introduction")
        up_intro_tfile.close()
        up_conclu_tfile = open(os.path.join(temp, self.minituto.get_phy_slug(), self.minituto.conclusion), "a")
        up_conclu_tfile.write(u"preuve de modification de la conclusion")
        up_conclu_tfile.close()

        # zip directory
        shutil.make_archive(os.path.join(temp, self.minituto.get_phy_slug()),
                            "zip",
                            os.path.join(temp, self.minituto.get_phy_slug()))

        self.assertTrue(os.path.isfile(os.path.join(temp, self.minituto.get_phy_slug() + ".zip")))
        # import zip archive
        result = self.client.post(
            reverse('zds.tutorial.views.import_tuto'),
            {
                'file': open(
                    os.path.join(
                        temp,
                        os.path.join(temp, self.minituto.get_phy_slug() + ".zip")),
                    'r'),
                'tutorial': self.minituto.pk,
                'import-archive': "importer"},
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Tutorial.objects.all().count(), 1)

        # delete temporary data directory
        shutil.rmtree(temp)
        os.remove(zip_path)

    def test_fail_import_archive(self):

        login_check = self.client.login(
            username=self.user_author.username,
            password='hostel77')
        self.assertEqual(login_check, True)

        temp = os.path.join(tempfile.gettempdir(), "temp")
        if not os.path.exists(temp):
            os.makedirs(temp, mode=0777)

        # test fail import
        with open(os.path.join(temp, 'test.py'), 'a') as f:
            f.write('something')

        result = self.client.post(
            reverse('zds.tutorial.views.import_tuto'),
            {
                'file': open(
                    os.path.join(
                        temp,
                        'test.py'),
                    'r'),
                'tutorial': self.minituto.pk,
                'import-archive': "importer"},
            follow=False
        )
        self.assertEqual(result.status_code, 200)

        # delete temporary data directory
        shutil.rmtree(temp)

    def test_add_extract_named_introduction(self):
        """test the use of an extract named introduction"""

        self.client.login(username=self.user_author,
                          password='hostel77')

        result = self.client.post(
            reverse('zds.tutorial.views.add_extract') +
            '?chapitre={0}'.format(
                self.chapter.pk),

            {
                'title': "Introduction",
                'text': u"Le contenu de l'extrait"
            })
        self.assertEqual(result.status_code, 302)
        tuto = Tutorial.objects.get(pk=self.minituto.pk)
        self.assertEqual(Extract.objects.all().count(), 1)
        intro_path = os.path.join(tuto.get_path(), "introduction.md")
        extract_path = Extract.objects.first().get_path()
        self.assertNotEqual(intro_path, extract_path)
        self.assertTrue(os.path.isfile(intro_path))
        self.assertTrue(os.path.isfile(extract_path))

    def test_add_extract_named_conclusion(self):
        """test the use of an extract named conclusion"""

        self.client.login(username=self.user_author,
                          password='hostel77')

        result = self.client.post(
            reverse('zds.tutorial.views.add_extract') +
            '?chapitre={0}'.format(
                self.chapter.pk),

            {
                'title': "Conclusion",
                'text': u"Le contenu de l'extrait"
            })
        self.assertEqual(result.status_code, 302)
        tuto = Tutorial.objects.get(pk=self.minituto.pk)
        self.assertEqual(Extract.objects.all().count(), 1)
        ccl_path = os.path.join(tuto.get_path(), "conclusion.md")
        extract_path = Extract.objects.first().get_path()
        self.assertNotEqual(ccl_path, extract_path)
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
        first_note = Note.objects.first()
        self.assertEqual(first_note.tutorial, tuto)
        self.assertEqual(first_note.author.pk, user1.pk)
        self.assertEqual(first_note.position, 1)
        self.assertEqual(first_note.pk, tuto.last_note.pk)
        self.assertEqual(
            Note.objects.first().text,
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
        """Test import of mini tuto."""
        result = self.client.post(
            reverse('zds.tutorial.views.import_tuto'),
            {
                'file': open(
                    os.path.join(
                        settings.BASE_DIR,
                        'fixtures',
                        'tuto',
                        'securisez-vos-mots-de-passe-avec-lastpass',
                        'securisez-vos-mots-de-passe-avec-lastpass.tuto'),
                    'r'),
                'images': open(
                    os.path.join(
                        settings.BASE_DIR,
                        'fixtures',
                        'tuto',
                        'securisez-vos-mots-de-passe-avec-lastpass',
                        'images.zip'),
                    'r'),
                'import-tuto': "importer"},
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

    def test_add_remove_authors(self):
        user1 = ProfileFactory().user

        # Add and remove author as simple user (not staff):
        login_check = self.client.login(
            username=self.user.username,
            password='hostel77')
        self.assertEqual(login_check, True)

        result = self.client.post(
            reverse('zds.tutorial.views.modify_tutorial'),
            {
                'author': user1.username,
                'tutorial': self.minituto.pk,
                'add_author': True,
            },
            follow=False)
        self.assertEqual(result.status_code, 403)

        result = self.client.post(
            reverse('zds.tutorial.views.modify_tutorial'),
            {
                'author': user1.pk,
                'tutorial': self.minituto.pk,
                'remove_author': True,
            },
            follow=False)
        self.assertEqual(result.status_code, 403)

        # Add and remove author as staff:
        login_check = self.client.login(
            username=self.staff.username,
            password='hostel77')
        self.assertEqual(login_check, True)

        result = self.client.post(
            reverse('zds.tutorial.views.modify_tutorial'),
            {
                'author': user1.username,
                'tutorial': self.minituto.pk,
                'add_author': True,
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        result = self.client.post(
            reverse('zds.tutorial.views.modify_tutorial'),
            {
                'author': user1.pk,
                'tutorial': self.minituto.pk,
                'remove_author': True,
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

    def test_delete_image_tutorial(self):
        """To test delete image of a tutorial."""
        # Author of the tutorial and the gallery (read and write permissions).
        login_check = self.client.login(username=self.user_author.username, password='hostel77')
        self.assertTrue(login_check)

        # Attach an image of a gallery at a tutorial.
        image_tutorial = ImageFactory(gallery=self.minituto.gallery)
        UserGalleryFactory(user=self.user_author, gallery=self.minituto.gallery)

        self.minituto.image = image_tutorial
        self.minituto.save()

        self.assertTrue(Tutorial.objects.get(pk=self.minituto.pk).image is not None)

        # Delete the image of the minituto.

        response = self.client.post(
            reverse('gallery-image-delete'),
            {
                'gallery': self.minituto.gallery.pk,
                'delete_multi': '',
                'items': [image_tutorial.pk]
            },
            follow=True
        )
        self.assertEqual(200, response.status_code)

        # Check if the tutorial is already in database and it doesn't have image.
        self.assertEqual(1, Tutorial.objects.filter(pk=self.minituto.pk).count())
        self.assertTrue(Tutorial.objects.get(pk=self.minituto.pk).image is None)

    def test_edit_tuto(self):
        "test that edition work well and avoid issue 1058"
        sub = SubCategory()
        sub.title = "toto"
        sub.save()
        # logout before
        self.client.logout()
        # first, login with author :
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)
        # edit the tuto without slug change
        response = self.client.post(
            reverse('zds.tutorial.views.edit_tutorial') + "?tutoriel={0}".format(self.minituto.pk),
            {
                'title': self.minituto.title,
                'description': "nouvelle description",
                'subcategory': [sub.pk],
                'introduction': self.minituto.get_introduction(),
                'conclusion': self.minituto.get_conclusion(),
                'licence': self.minituto.licence.pk,
                'last_hash': compute_hash([os.path.join(self.minituto.get_path(), "introduction.md"),
                                           os.path.join(self.minituto.get_path(), "conclusion.md")])
            },
            follow=False
        )
        self.assertEqual(302, response.status_code)
        tuto = Tutorial.objects.filter(pk=self.minituto.pk).first()
        self.assertEqual(tuto.title, self.minituto.title)
        self.assertEqual(tuto.description, "nouvelle description")
        # edit tuto with a slug change
        (introduction, conclusion) = (self.minituto.get_introduction(), self.minituto.get_conclusion())
        self.client.post(
            reverse('zds.tutorial.views.edit_tutorial') + "?tutoriel={0}".format(self.minituto.pk),
            {
                'title': "nouveau titre pour nouveau slug",
                'description': "nouvelle description",
                'subcategory': [sub.pk],
                'introduction': introduction,
                'conclusion': conclusion,
                'licence': self.minituto.licence.pk,
                'last_hash': compute_hash([os.path.join(self.minituto.get_path(), "introduction.md"),
                                           os.path.join(self.minituto.get_path(), "conclusion.md")])
            },
            follow=False
        )
        tuto = Tutorial.objects.filter(pk=self.minituto.pk).first()
        self.assertEqual(tuto.title, "nouveau titre pour nouveau slug")
        self.assertEqual(tuto.description, "nouvelle description")
        self.assertEqual(introduction, tuto.get_introduction())

    def test_reorder_tuto(self):
        "test that reordering makes it good to avoid #1060"
        # logout before
        self.client.logout()
        # first, login with author :
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)
        introduction = self.minituto.get_introduction()
        # prepare the extracts
        self.client.post(
            reverse('zds.tutorial.views.add_extract') + "?chapitre={0}".format(self.minituto.get_chapter().pk),
            {

                'title': "extract 1",
                'text': "extract 1 text"
            },
            follow=False
        )
        extract_pk = Tutorial.objects.get(pk=self.minituto.pk).get_chapter().get_extracts()[0].pk
        self.client.post(
            reverse('zds.tutorial.views.add_extract') + "?chapitre={0}".format(self.minituto.get_chapter().pk),
            {

                'title': "extract 2",
                'text': "extract 2 text"
            },
            follow=False
        )
        self.assertEqual(2, self.minituto.get_chapter().get_extracts().count())
        # reorder
        self.client.post(
            reverse('zds.tutorial.views.modify_extract'),
            {
                'move': "",
                'move_target': 2,
                'extract': self.minituto.get_chapter().get_extracts()[0].pk
            },
            follow=False
        )
        # this test check issue 1060
        self.assertEqual(introduction, Tutorial.objects.filter(pk=self.minituto.pk).first().get_introduction())
        self.assertEqual(2, Extract.objects.get(pk=extract_pk).position_in_chapter)

    def test_workflow_beta_tuto(self):
        "Ensure the behavior of the beta version of tutorials"

        ForumFactory(
            category=CategoryFactory(position=1),
            position_in_category=1)

        # logout before
        self.client.logout()

        # check if acess to page with beta tutorial (with guest)
        response = self.client.get(
            reverse(
                'zds.tutorial.views.find_tuto',
                args=[self.user_author.pk]
            ) + '?type=beta'
        )
        self.assertEqual(200, response.status_code)

        # first, login with author :
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)
        # then active the beta on tutorial :
        sha_draft = Tutorial.objects.get(pk=self.minituto.pk).sha_draft
        response = self.client.post(
            reverse('zds.tutorial.views.modify_tutorial'),
            {
                'tutorial': self.minituto.pk,
                'activ_beta': True,
                'version': sha_draft
            },
            follow=False
        )
        self.assertEqual(302, response.status_code)

        # check if acess to page with beta tutorial (with author)
        response = self.client.get(
            reverse(
                'zds.tutorial.views.find_tuto',
                args=[self.user_author.pk]
            ) + '?type=beta'
        )
        self.assertEqual(200, response.status_code)
        # test beta :
        self.assertEqual(
            Tutorial.objects.get(pk=self.minituto.pk).sha_beta,
            sha_draft)
        url = Tutorial.objects.get(pk=self.minituto.pk).get_absolute_url_beta()
        sha_beta = sha_draft
        # Test access for author (get 200)
        self.assertEqual(
            self.client.get(url).status_code,
            200)
        # test access from outside (get 302, connexion form)
        self.client.logout()
        self.assertEqual(
            self.client.get(url).status_code,
            302)
        # test access for random user (get 200)
        self.assertEqual(
            self.client.login(
                username=self.user.username,
                password='hostel77'),
            True)
        self.assertEqual(
            self.client.get(url).status_code,
            200)

        # check if acess to page with beta tutorial (with random user)
        response = self.client.get(
            reverse(
                'zds.tutorial.views.find_tuto',
                args=[self.user_author.pk]
            ) + '?type=beta'
        )
        self.assertEqual(200, response.status_code)

        # then modify tutorial
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)
        result = self.client.post(
            reverse('zds.tutorial.views.add_extract') +
            '?chapitre={0}'.format(
                self.chapter.pk),

            {
                'title': "Introduction",
                'text': u"Le contenu de l'extrait"
            })
        self.assertEqual(result.status_code, 302)
        self.assertEqual(
            Tutorial.objects.get(pk=self.minituto.pk).sha_beta,
            sha_beta)
        self.assertNotEqual(
            Tutorial.objects.get(pk=self.minituto.pk).sha_draft,
            sha_beta)
        # update beta
        sha_draft = Tutorial.objects.get(pk=self.minituto.pk).sha_draft
        response = self.client.post(
            reverse('zds.tutorial.views.modify_tutorial'),
            {
                'tutorial': self.minituto.pk,
                'update_beta': True,
                'version': sha_draft
            },
            follow=False
        )
        self.assertEqual(302, response.status_code)
        url = Tutorial.objects.get(pk=self.minituto.pk).get_absolute_url_beta()
        # test access to new beta url (get 200) :
        self.assertEqual(
            self.client.get(url).status_code,
            200)
        # test access for random user to new url (get 200) and old (get 403)
        self.assertEqual(
            self.client.login(
                username=self.user.username,
                password='hostel77'),
            True)
        self.assertEqual(
            self.client.get(url).status_code,
            200)

        # then desactive beta :
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)
        response = self.client.post(
            reverse('zds.tutorial.views.modify_tutorial'),
            {
                'tutorial': self.minituto.pk,
                'desactiv_beta': True,
                'version': sha_draft
            },
            follow=False
        )
        self.assertEqual(302, response.status_code)
        self.assertEqual(
            Tutorial.objects.get(pk=self.minituto.pk).sha_beta,
            None)
        # test access from outside (get 302, connexion form)
        self.client.logout()
        self.assertEqual(
            self.client.get(url).status_code,
            302)
        # test access for random user (get 403)
        self.assertEqual(
            self.client.login(
                username=self.user.username,
                password='hostel77'),
            True)
        self.assertEqual(
            self.client.get(url).status_code,
            403)

        # ensure staff behavior (staff can also active/update/desactive beta)
        self.assertEqual(
            self.client.login(
                username=self.staff.username,
                password='hostel77'),
            True)
        response = self.client.post(
            reverse('zds.tutorial.views.modify_tutorial'),
            {
                'tutorial': self.minituto.pk,
                'activ_beta': True,
                'version': sha_draft
            },
            follow=False
        )
        self.assertEqual(302, response.status_code)
        # test access from outside (get 302, connexion form)
        self.client.logout()
        self.assertEqual(
            self.client.get(url).status_code,
            302)
        # test access for random user (get 200)
        self.assertEqual(
            self.client.login(
                username=self.user.username,
                password='hostel77'),
            True)
        self.assertEqual(
            self.client.get(url).status_code,
            200)

    def test_workflow_tuto(self):
        """Test workflow of mini tutorial."""

        ForumFactory(
            category=CategoryFactory(position=1),
            position_in_category=1)

        # logout before
        self.client.logout()
        # login with simple member
        self.assertEqual(
            self.client.login(
                username=self.user.username,
                password='hostel77'),
            True)

        # add new mini tuto
        result = self.client.post(
            reverse('zds.tutorial.views.add_tutorial'),
            {
                'title': u"Introduction à l'algèbre",
                'description': "Perçer les mystère de boole",
                'introduction': "Bienvenue dans le monde binaires",
                'conclusion': "",
                'type': "MINI",
                'licence': self.licence.pk,
                'subcategory': self.subcat.pk,
            },
            follow=False)

        self.assertEqual(result.status_code, 302)
        self.assertEqual(Tutorial.objects.all().count(), 2)
        tuto = Tutorial.objects.last()
        chapter = Chapter.objects.filter(tutorial__pk=tuto.pk).first()

        # add extract 1
        result = self.client.post(
            reverse('zds.tutorial.views.add_extract') + '?chapitre={}'.format(chapter.pk),
            {
                'title': u"Extrait 1",
                'text': u"Introduisons notre premier extrait",
            },
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Extract.objects.filter(chapter=chapter).count(), 1)
        e1 = Extract.objects.filter(chapter=chapter).last()

        # check view offline
        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_tutorial',
                args=[
                    tuto.pk,
                    tuto.slug]),
            follow=True)
        self.assertContains(response=result, text=u"Extrait 1")
        self.assertContains(response=result, text=u"Introduisons notre premier extrait")

        # add extract 2
        result = self.client.post(
            reverse('zds.tutorial.views.add_extract') + '?chapitre={}'.format(chapter.pk),
            {
                'title': u"Extrait 2",
                'text': u"Introduisons notre deuxième extrait",
            },
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Extract.objects.filter(chapter=chapter).count(), 2)
        e2 = Extract.objects.filter(chapter=chapter).last()

        # check view offline
        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_tutorial',
                args=[
                    tuto.pk,
                    tuto.slug]),
            follow=True)
        self.assertContains(response=result, text=u"Extrait 2")
        self.assertContains(response=result, text=u"Introduisons notre deuxième extrait")

        # add extract 3
        result = self.client.post(
            reverse('zds.tutorial.views.add_extract') + '?chapitre={}'.format(chapter.pk),
            {
                'title': u"Extrait 3",
                'text': u"Introduisons notre troisième extrait",
            },
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Extract.objects.filter(chapter=chapter).count(), 3)
        Extract.objects.filter(chapter=chapter).last()

        # check view offline
        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_tutorial',
                args=[
                    tuto.pk,
                    tuto.slug]),
            follow=True)
        self.assertContains(response=result, text=u"Extrait 3")
        self.assertContains(response=result, text=u"Introduisons notre troisième extrait")

        # edit extract 2
        result = self.client.post(
            reverse('zds.tutorial.views.edit_extract') + '?extrait={}'.format(e2.pk),
            {
                'title': u"Extrait 2 : edition de titre",
                'text': u"Edition d'introduction",
                "last_hash": compute_hash([e2.get_path()])
            },
            follow=True)
        self.assertEqual(result.status_code, 200)
        self.assertContains(response=result, text=u"Extrait 2 : edition de titre")
        self.assertContains(response=result, text=u"Edition d'introduction")
        self.assertEqual(Extract.objects.filter(chapter__tutorial=tuto).count(), 3)

        # move extract 1 against 2
        result = self.client.post(
            reverse('zds.tutorial.views.modify_extract'),
            {
                'extract': e1.pk,
                'move_target': e2.position_in_chapter,
            },
            follow=True)

        # delete extract 1
        result = self.client.post(
            reverse('zds.tutorial.views.modify_extract'),
            {
                'extract': e1.pk,
                'delete': "OK",
            },
            follow=True)

        self.assertEqual(Extract.objects.filter(chapter__tutorial=tuto).count(), 2)

    def test_workflow_licence(self):
        '''Ensure the behavior of licence on mini-tutorials'''

        # create a new licence
        new_licence = LicenceFactory(code='CC_BY', title='Creative Commons BY')
        new_licence = Licence.objects.get(pk=new_licence.pk)

        # check value first
        tuto = Tutorial.objects.get(pk=self.minituto.pk)
        self.assertEqual(tuto.licence.pk, self.licence.pk)

        # get value wich does not change (speed up test)
        introduction = self.minituto.get_introduction()
        conclusion = self.minituto.get_conclusion()
        hash = compute_hash([
            os.path.join(self.minituto.get_path(), "introduction.md"),
            os.path.join(self.minituto.get_path(), "conclusion.md")
        ])

        # logout before
        self.client.logout()
        # login with author
        self.assertTrue(
            self.client.login(
                username=self.user_author.username,
                password='hostel77')
        )

        # change licence (get 302) :
        result = self.client.post(
            reverse('zds.tutorial.views.edit_tutorial') +
            '?tutoriel={}'.format(self.minituto.pk),
            {
                'title': self.minituto.title,
                'description': self.minituto.description,
                'introduction': introduction,
                'conclusion': conclusion,
                'subcategory': self.subcat.pk,
                'licence': new_licence.pk,
                'last_hash': hash
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        # test change :
        tuto = Tutorial.objects.get(pk=self.minituto.pk)
        self.assertNotEqual(tuto.licence.pk, self.licence.pk)
        self.assertEqual(tuto.licence.pk, new_licence.pk)

        # test change in JSON :
        json = tuto.load_json()
        self.assertEquals(json['licence'], new_licence.code)

        # then logout ...
        self.client.logout()
        # ... and login with staff
        self.assertTrue(
            self.client.login(
                username=self.staff.username,
                password='hostel77')
        )

        # change licence back to old one (get 302, staff can change licence) :
        result = self.client.post(
            reverse('zds.tutorial.views.edit_tutorial') +
            '?tutoriel={}'.format(self.minituto.pk),
            {
                'title': self.minituto.title,
                'description': self.minituto.description,
                'introduction': introduction,
                'conclusion': conclusion,
                'subcategory': self.subcat.pk,
                'licence': self.licence.pk,
                'last_hash': hash
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        # test change :
        tuto = Tutorial.objects.get(pk=self.minituto.pk)
        self.assertEqual(tuto.licence.pk, self.licence.pk)
        self.assertNotEqual(tuto.licence.pk, new_licence.pk)

        # test change in JSON :
        json = tuto.load_json()
        self.assertEquals(json['licence'], self.licence.code)

        # then logout ...
        self.client.logout()

        # change licence (get 302, redirection to login page) :
        result = self.client.post(
            reverse('zds.tutorial.views.edit_tutorial') +
            '?tutoriel={}'.format(self.minituto.pk),
            {
                'title': self.minituto.title,
                'description': self.minituto.description,
                'introduction': introduction,
                'conclusion': conclusion,
                'subcategory': self.subcat.pk,
                'licence': new_licence.pk,
                'last_hash': hash
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        # test change (normaly, nothing has) :
        tuto = Tutorial.objects.get(pk=self.minituto.pk)
        self.assertEqual(tuto.licence.pk, self.licence.pk)
        self.assertNotEqual(tuto.licence.pk, new_licence.pk)

        # login with random user
        self.assertTrue(
            self.client.login(
                username=self.user.username,
                password='hostel77')
        )

        # change licence (get 403, random user cannot edit minituto if not in
        # authors list) :
        result = self.client.post(
            reverse('zds.tutorial.views.edit_tutorial') +
            '?tutoriel={}'.format(self.minituto.pk),
            {
                'title': self.minituto.title,
                'description': self.minituto.description,
                'introduction': introduction,
                'conclusion': conclusion,
                'subcategory': self.subcat.pk,
                'licence': new_licence.pk,
                'last_hash': hash
            },
            follow=False)
        self.assertEqual(result.status_code, 403)

        # test change (normaly, nothing has) :
        tuto = Tutorial.objects.get(pk=self.minituto.pk)
        self.assertEqual(tuto.licence.pk, self.licence.pk)
        self.assertNotEqual(tuto.licence.pk, new_licence.pk)

        # test change in JSON (normaly, nothing has) :
        json = tuto.load_json()
        self.assertEquals(json['licence'], self.licence.code)

    def test_workflow_archive_tuto(self):
        """ensure the behavior of archive with a mini tutorial"""

        # login with author
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)

        # modify tutorial, add a new extract (NOTE: zipfile does not ensure UTF-8) :
        extract_title = u'Un titre d\'extrait'
        extract_content = u'To be or not to be, that\'s the question (extract of Hamlet)'
        result = self.client.post(
            reverse('zds.tutorial.views.add_extract') +
            '?chapitre={0}'.format(
                self.chapter.pk),
            {
                'title': extract_title,
                'text': extract_content
            })
        self.assertEqual(result.status_code, 302)

        # now, draft and public version are not the same
        tutorial = Tutorial.objects.get(pk=self.minituto.pk)
        self.assertNotEqual(tutorial.sha_draft, tutorial.sha_public)
        # store extract
        added_extract = Extract.objects.get(chapter=Chapter.objects.get(pk=self.chapter.pk))

        # fetch archives :
        # 1. draft version
        result = self.client.get(
            reverse('zds.tutorial.views.download') +
            '?tutoriel={0}'.format(
                self.minituto.pk),
            follow=False)
        self.assertEqual(result.status_code, 200)
        draft_zip_path = os.path.join(tempfile.gettempdir(), '__draft.zip')
        f = open(draft_zip_path, 'w')
        f.write(result.content)
        f.close()
        # 2. online version :
        result = self.client.get(
            reverse('zds.tutorial.views.download') +
            '?tutoriel={0}&online'.format(
                self.minituto.pk),
            follow=False)
        self.assertEqual(result.status_code, 200)
        online_zip_path = os.path.join(tempfile.gettempdir(), '__online.zip')
        f = open(online_zip_path, 'w')
        f.write(result.content)
        f.close()

        # now check if modification are in draft version of archive and not in the public one
        draft_zip = zipfile.ZipFile(draft_zip_path, 'r')
        online_zip = zipfile.ZipFile(online_zip_path, 'r')

        # first, test in manifest
        online_manifest = json_reader.loads(online_zip.read('manifest.json'))
        found = False
        for extract in online_manifest['chapter']['extracts']:
            if extract['pk'] == added_extract.pk:
                found = True
        self.assertFalse(found)  # extract cannot exists in the online version

        draft_manifest = json_reader.loads(draft_zip.read('manifest.json'))
        extract_in_manifest = []
        for extract in draft_manifest['chapter']['extracts']:
            if extract['pk'] == added_extract.pk:
                found = True
                extract_in_manifest = extract
        self.assertTrue(found)  # extract exists in draft version
        self.assertEqual(extract_in_manifest['title'], extract_title)

        # and then, test the file directly :
        found = True
        try:
            online_zip.getinfo(extract_in_manifest['text'])
        except KeyError:
            found = False
        self.assertFalse(found)  # extract cannot exists in the online version

        found = True
        try:
            draft_zip.getinfo(extract_in_manifest['text'])
        except KeyError:
            found = False
        self.assertTrue(found)  # extract exists in the draft one
        self.assertEqual(draft_zip.read(extract_in_manifest['text']), extract_content)  # content is good

        draft_zip.close()
        online_zip.close()

        # then logout and test access
        self.client.logout()

        # public cannot access to draft version of tutorial
        result = self.client.get(
            reverse('zds.tutorial.views.download') +
            '?tutoriel={0}'.format(
                self.minituto.pk),
            follow=False)
        self.assertEqual(result.status_code, 403)
        # ... but can access to online version
        result = self.client.get(
            reverse('zds.tutorial.views.download') +
            '?tutoriel={0}&online'.format(
                self.minituto.pk),
            follow=False)
        self.assertEqual(result.status_code, 200)

        # login with random user
        self.assertEqual(
            self.client.login(
                username=self.user.username,
                password='hostel77'),
            True)

        # cannot access to draft version of tutorial (if not author or staff)
        result = self.client.get(
            reverse('zds.tutorial.views.download') +
            '?tutoriel={0}'.format(
                self.minituto.pk),
            follow=False)
        self.assertEqual(result.status_code, 403)
        # but can access to online one
        result = self.client.get(
            reverse('zds.tutorial.views.download') +
            '?tutoriel={0}&online'.format(
                self.minituto.pk),
            follow=False)
        self.assertEqual(result.status_code, 200)
        self.client.logout()

        # login with staff user
        self.assertEqual(
            self.client.login(
                username=self.staff.username,
                password='hostel77'),
            True)

        # staff can access to draft version of tutorial
        result = self.client.get(
            reverse('zds.tutorial.views.download') +
            '?tutoriel={0}'.format(
                self.minituto.pk),
            follow=False)
        self.assertEqual(result.status_code, 200)
        # ... and also to online version
        result = self.client.get(
            reverse('zds.tutorial.views.download') +
            '?tutoriel={0}&online'.format(
                self.minituto.pk),
            follow=False)
        self.assertEqual(result.status_code, 200)

        # finally, clean up things:
        os.remove(draft_zip_path)
        os.remove(online_zip_path)

    def test_help_to_perfect_tuto(self):
        """ This test aim to unit test the "help me to write my tutorial"
        interface. It is testing if the back-end is always sending back
        good datas """

        helps = HelpWriting.objects.all()

        # currently the tutorial is published with no beta, so back-end should return 0 tutorial
        response = self.client.post(
            reverse('zds.tutorial.views.help_tutorial'),
            follow=False
        )
        self.assertEqual(200, response.status_code)
        tutos = response.context['tutorials']
        self.assertEqual(len(tutos), 0)

        # then active the beta on tutorial :
        ForumFactory(
            category=CategoryFactory(position=1),
            position_in_category=1)
        # first, login with author :
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)
        sha_draft = Tutorial.objects.get(pk=self.minituto.pk).sha_draft
        response = self.client.post(
            reverse('zds.tutorial.views.modify_tutorial'),
            {
                'tutorial': self.minituto.pk,
                'activ_beta': True,
                'version': sha_draft
            },
            follow=False
        )
        self.assertEqual(302, response.status_code)
        sha_beta = Tutorial.objects.get(pk=self.minituto.pk).sha_beta
        self.assertEqual(sha_draft, sha_beta)
        response = self.client.post(
            reverse('zds.tutorial.views.help_tutorial'),
            follow=False
        )
        self.assertEqual(200, response.status_code)
        tutos = response.context['tutorials']
        self.assertEqual(len(tutos), 1)

        # However if we ask with a filter we will still get 0
        for helping in helps:
            response = self.client.post(
                reverse('zds.tutorial.views.help_tutorial') +
                u'?type={}'.format(helping.slug),
                follow=False
            )
            self.assertEqual(200, response.status_code)
            tutos = response.context['tutorials']
            self.assertEqual(len(tutos), 0)

        # now tutorial is positive for every options
        # if we ask for any help we should get a positive answer for every filter
        for helping in helps:
            self.minituto.helps.add(helping)
        self.minituto.save()

        for helping in helps:
            response = self.client.post(
                reverse('zds.tutorial.views.help_tutorial') +
                u'?type={}'.format(helping.slug),
                follow=False
            )
            self.assertEqual(200, response.status_code)
            tutos = response.context['tutorials']
            self.assertEqual(len(tutos), 1)

        # test pagination page doesn't exist
        response = self.client.post(
            reverse('zds.tutorial.views.help_tutorial') +
            u'?page=1534',
            follow=False
        )
        self.assertEqual(404, response.status_code)

        # test pagination page not an integer
        response = self.client.post(
            reverse('zds.tutorial.views.help_tutorial') +
            u'?page=abcd',
            follow=False
        )
        self.assertEqual(404, response.status_code)

    def test_change_update(self):
        """test the change of `tutorial.update` if extract is modified (ensure #1715)"""

        # login with author
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)

        time_0 = datetime.datetime.fromtimestamp(0)  # way deep in the past
        tutorial = Tutorial.objects.get(pk=self.minituto.pk)
        tutorial.update = time_0
        tutorial.save()

        # first check if this modification is performed :
        self.assertEqual(Tutorial.objects.get(pk=self.minituto.pk).update, time_0)

        # test adding a new extract (implicit call to `maj_repo_extract()`)
        result = self.client.post(
            reverse('zds.tutorial.views.add_extract') +
            '?chapitre={0}'.format(
                self.chapter.pk),
            {
                'title': u'Un deuxieme extrait',
                'text': u'Attention aux épines, ça pique !!'
            })
        self.assertEqual(result.status_code, 302)

        tutorial = Tutorial.objects.get(pk=self.minituto.pk)
        self.assertNotEqual(tutorial.update, time_0)
        tutorial.update = time_0
        tutorial.save()

        # test the extract edition (also implicit call to `maj_repo_extract()`) :
        extract = self.chapter.get_extracts().last()
        result = self.client.post(
            reverse('zds.tutorial.views.edit_extract') + '?extrait={}'.format(extract.pk),
            {
                'title': u"Un autre titre",
                'text': u"j'ai changé d'avis, je vais mettre un sapin synthétique",
                "last_hash": compute_hash([extract.get_path()])
            },
            follow=True)
        self.assertEqual(result.status_code, 200)
        self.assertNotEqual(Tutorial.objects.get(pk=self.minituto.pk).update, time_0)

    def test_warn_typo(self):
        """
        Add a non-regression test about warning the author(s) of a typo in tutorial
        """

        bot = Group(name=settings.ZDS_APP["member"]["bot_group"])
        bot.save()

        typo_text = u'T\'as fait une faute, t\'es nul'

        # login with author
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)

        # check if author get error when warning typo on its own tutorial
        result = self.client.post(
            reverse('zds.tutorial.views.warn_typo', args=[u"tutorial", self.minituto.pk]),
            {
                'explication': u'ceci est un test',
                'version_tutorial': self.minituto.sha_public
            },
            follow=True)
        self.assertEqual(result.status_code, 200)

        msgs = result.context['messages']
        last = None
        for msg in msgs:
            last = msg
        self.assertEqual(last.level, messages.ERROR)

        # login with normal user
        self.client.logout()

        self.assertEqual(
            self.client.login(
                username=self.user.username,
                password='hostel77'),
            True)

        # check if user can warn typo in tutorial
        result = self.client.post(
            reverse('zds.tutorial.views.warn_typo', args=[u"tutorial", self.minituto.pk]),
            {
                'explication': typo_text,
                'version_tutorial': self.minituto.sha_public
            },
            follow=True)
        self.assertEqual(result.status_code, 200)

        msgs = result.context['messages']
        last = None
        for msg in msgs:
            last = msg
        self.assertEqual(last.level, messages.SUCCESS)

        # check PM :
        sent_pm = PrivateTopic.objects.filter(author=self.user.pk).last()
        self.assertIn(self.user_author, sent_pm.participants.all())  # author is in participants
        self.assertIn(typo_text, sent_pm.last_message.text)  # typo is in message
        self.assertIn(self.minituto.get_absolute_url_online(), sent_pm.last_message.text)  # public url is in message

        # induce a change and put in beta :
        self.client.logout()

        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)

        result = self.client.post(
            reverse('zds.tutorial.views.add_extract') + '?chapitre={0}'.format(self.chapter.pk),
            {
                'title': u'Un nouveau titre d\'extrait',
                'text': u'Linux is like sex, it\'s better when it\'s free (L. Torvald)'
            })
        self.assertEqual(result.status_code, 302)

        sha_draft = Tutorial.objects.get(pk=self.minituto.pk).sha_draft
        response = self.client.post(
            reverse('zds.tutorial.views.modify_tutorial'),
            {
                'tutorial': self.minituto.pk,
                'activ_beta': True,
                'version': sha_draft
            },
            follow=False
        )
        self.assertEqual(302, response.status_code)

        # login with normal user
        self.client.logout()

        self.assertEqual(
            self.client.login(
                username=self.user.username,
                password='hostel77'),
            True)

        # check if user can warn typo in tutorial in beta version
        result = self.client.post(
            reverse('zds.tutorial.views.warn_typo', args=[u"tutorial", self.minituto.pk]),
            {
                'explication': typo_text,
                'version_tutorial': Tutorial.objects.get(pk=self.minituto.pk).sha_beta
            },
            follow=True)
        self.assertEqual(result.status_code, 200)

        msgs = result.context['messages']
        last = None
        for msg in msgs:
            last = msg
        self.assertEqual(last.level, messages.SUCCESS)

        # check PM :
        sent_pm = PrivateTopic.objects.filter(author=self.user.pk).last()
        self.assertIn(self.user_author, sent_pm.participants.all())  # author is in participants
        self.assertIn(typo_text, sent_pm.last_message.text)  # typo is in message
        self.assertIn(Tutorial.objects.get(pk=self.minituto.pk).get_absolute_url_beta(),
                      sent_pm.last_message.text)  # beta url is in message !

    def tearDown(self):
        if os.path.isdir(settings.ZDS_APP['tutorial']['repo_path']):
            shutil.rmtree(settings.ZDS_APP['tutorial']['repo_path'])
        if os.path.isdir(settings.ZDS_APP['tutorial']['repo_public_path']):
            shutil.rmtree(settings.ZDS_APP['tutorial']['repo_public_path'])
        if os.path.isdir(settings.ZDS_APP['article']['repo_path']):
            shutil.rmtree(settings.ZDS_APP['article']['repo_path'])
        if os.path.isdir(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)
