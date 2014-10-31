# coding: utf-8

import os
import shutil
import tempfile
import zipfile
from git import Repo
try:
    import ujson as json_reader
except:
    try:
        import simplejson as json_reader
    except:
        import json as json_reader
from django.db.models import Q
from django.conf import settings
from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings

from zds.forum.factories import CategoryFactory, ForumFactory
from zds.member.factories import ProfileFactory, StaffProfileFactory
from zds.gallery.factories import UserGalleryFactory, ImageFactory
from zds.mp.models import PrivateTopic
from zds.settings import SITE_ROOT
from zds.tutorial.factories import BigTutorialFactory, MiniTutorialFactory, PartFactory, \
    ChapterFactory, NoteFactory, SubCategoryFactory, LicenceFactory
from zds.gallery.factories import GalleryFactory
from zds.tutorial.models import Note, PubliableContent, Validation, Extract, Part, Chapter
from zds.tutorial.views import insert_into_zip
from zds.utils.models import SubCategory, Licence, Alert
from zds.utils.misc import compute_hash


@override_settings(MEDIA_ROOT=os.path.join(SITE_ROOT, 'media-test'))
@override_settings(REPO_PATH=os.path.join(SITE_ROOT, 'tutoriels-private-test'))
@override_settings(REPO_PATH_PROD=os.path.join(SITE_ROOT, 'tutoriels-public-test'))
@override_settings(REPO_ARTICLE_PATH=os.path.join(SITE_ROOT, 'articles-data-test'))
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

        self.licence = LicenceFactory()
        self.licence.save()

        self.bigtuto = BigTutorialFactory()
        self.bigtuto.authors.add(self.user_author)
        self.bigtuto.gallery = GalleryFactory()
        self.bigtuto.licence = self.licence
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
        self.bigtuto = PubliableContent.objects.get(pk=self.bigtuto.pk)
        self.assertEqual(pub.status_code, 302)
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

        self.assertTrue(os.path.isfile(os.path.join(temp, self.bigtuto.get_phy_slug()+".zip")))

        # import zip archive
        result = self.client.post(
            reverse('zds.tutorial.views.import_tuto'),
            {
                'file': open(
                    os.path.join(
                        temp,
                        os.path.join(temp, self.bigtuto.get_phy_slug()+".zip")),
                    'r'),
                'tutorial': self.bigtuto.pk,
                'import-archive': "importer"},
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(PubliableContent.objects.all().count(), 1)

        # delete temporary data directory
        shutil.rmtree(temp)
        os.remove(zip_path)

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
        tuto = PubliableContent.objects.get(pk=self.bigtuto.pk)
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
                    'r'),
                'import-tuto': "importer"},
            follow=False)
        self.assertEqual(result.status_code, 302)

        self.assertEqual(PubliableContent.objects.all().count(), 2)

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
        self.assertEqual(PubliableContent.objects.all().count(), 2)
        tuto = PubliableContent.objects.last()
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
        tuto = PubliableContent.objects.get(pk=tuto.pk)

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
        sha_draft = PubliableContent.objects.get(pk=tuto.pk).sha_draft
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
        sha_beta = PubliableContent.objects.get(pk=tuto.pk).sha_beta
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
                'zds.tutorial.views.view_part',
                args=[
                    tuto.pk,
                    tuto.slug,
                    p1.pk,
                    p1.slug]) + '?version={}'.format(sha_beta),
            follow=True)
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_chapter',
                args=[
                    tuto.pk,
                    tuto.slug,
                    p2.pk,
                    p2.slug,
                    c3.pk,
                    c3.slug]) + '?version={}'.format(sha_beta),
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
        tuto = PubliableContent.objects.get(pk=tuto.pk)
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
                'zds.tutorial.views.view_part',
                args=[
                    tuto.pk,
                    tuto.slug,
                    p1.pk,
                    p1.slug]) + '?version={}'.format(sha_beta),
            follow=True)
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_chapter',
                args=[
                    tuto.pk,
                    tuto.slug,
                    p2.pk,
                    p2.slug,
                    c3.pk,
                    c3.slug]) + '?version={}'.format(sha_beta),
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

        self.assertTrue(PubliableContent.objects.get(pk=self.bigtuto.pk).image is not None)

        # Delete the image of the bigtuto.

        response = self.client.post(
            reverse('zds.gallery.views.delete_image'),
            {
                'gallery': self.bigtuto.gallery.pk,
                'delete_multi': '',
                'items': [image_tutorial.pk]
            },
            follow=True
        )
        self.assertEqual(200, response.status_code)

        # Check if the tutorial is already in database and it doesn't have image.
        self.assertEqual(1, PubliableContent.objects.filter(pk=self.bigtuto.pk).count())
        self.assertTrue(PubliableContent.objects.get(pk=self.bigtuto.pk).image is None)

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
        sha_draft = PubliableContent.objects.get(pk=self.bigtuto.pk).sha_draft
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
            PubliableContent.objects.get(pk=self.bigtuto.pk).sha_beta,
            sha_draft)
        url = PubliableContent.objects.get(pk=self.bigtuto.pk).get_absolute_url_beta()
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
            PubliableContent.objects.get(pk=self.bigtuto.pk).sha_beta,
            sha_beta)
        self.assertNotEqual(
            PubliableContent.objects.get(pk=self.bigtuto.pk).sha_draft,
            sha_beta)
        # update beta
        sha_draft = PubliableContent.objects.get(pk=self.bigtuto.pk).sha_draft
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
        old_url = url
        url = PubliableContent.objects.get(pk=self.bigtuto.pk).get_absolute_url_beta()
        # test access to new beta url (get 200) :
        self.assertEqual(
            self.client.get(old_url).status_code,
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
        self.assertEqual(
            self.client.get(old_url).status_code,
            403)

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
            PubliableContent.objects.get(pk=self.bigtuto.pk).sha_beta,
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

        tuto = PubliableContent.objects.filter(pk=self.bigtuto.pk).first()
        self.assertEqual(tuto.title, newtitle)
        self.assertEqual(tuto.gallery.title, tuto.title)
        self.assertEqual(tuto.gallery.slug, tuto.slug)

    def test_workflow_licence(self):
        '''Ensure the behavior of licence on mini-tutorials'''

        # create a new licence
        new_licence = LicenceFactory(code='CC_BY', title='Creative Commons BY')
        new_licence = Licence.objects.get(pk=new_licence.pk)

        # check value first
        tuto = PubliableContent.objects.get(pk=self.bigtuto.pk)
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
        tuto = PubliableContent.objects.get(pk=self.bigtuto.pk)
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
        tuto = PubliableContent.objects.get(pk=self.bigtuto.pk)
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
        tuto = PubliableContent.objects.get(pk=self.bigtuto.pk)
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
        tuto = PubliableContent.objects.get(pk=self.bigtuto.pk)
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
        tutorial = PubliableContent.objects.get(pk=self.bigtuto.pk)
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

    def tearDown(self):
        if os.path.isdir(settings.ZDS_APP['tutorial']['repo_path']):
            shutil.rmtree(settings.ZDS_APP['tutorial']['repo_path'])
        if os.path.isdir(settings.ZDS_APP['tutorial']['repo_public_path']):
            shutil.rmtree(settings.ZDS_APP['tutorial']['repo_public_path'])
        if os.path.isdir(settings.ZDS_APP['article']['repo_path']):
            shutil.rmtree(settings.ZDS_APP['article']['repo_path'])
        if os.path.isdir(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)


@override_settings(MEDIA_ROOT=os.path.join(SITE_ROOT, 'media-test'))
@override_settings(REPO_PATH=os.path.join(SITE_ROOT, 'tutoriels-private-test'))
@override_settings(REPO_PATH_PROD=os.path.join(SITE_ROOT, 'tutoriels-public-test'))
@override_settings(REPO_ARTICLE_PATH=os.path.join(SITE_ROOT, 'articles-data-test'))
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

        self.licence = LicenceFactory()
        self.licence.save()

        self.minituto = MiniTutorialFactory()
        self.minituto.authors.add(self.user_author)
        self.minituto.gallery = GalleryFactory()
        self.minituto.licence = self.licence
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
        self.minituto = PubliableContent.objects.get(pk=self.minituto.pk)
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

        self.assertTrue(os.path.isfile(os.path.join(temp, self.minituto.get_phy_slug()+".zip")))
        # import zip archive
        result = self.client.post(
            reverse('zds.tutorial.views.import_tuto'),
            {
                'file': open(
                    os.path.join(
                        temp,
                        os.path.join(temp, self.minituto.get_phy_slug()+".zip")),
                    'r'),
                'tutorial': self.minituto.pk,
                'import-archive': "importer"},
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(PubliableContent.objects.all().count(), 1)

        # delete temporary data directory
        shutil.rmtree(temp)
        os.remove(zip_path)

    def add_test_extract_named_introduction(self):
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
        tuto = PubliableContent.objects.get(pk=self.minituto.pk)
        self.assertEqual(Extract.objects.all().count(), 1)
        intro_path = os.path.join(tuto.get_path(), "introduction.md")
        extract_path = Extract.objects.get(pk=1).get_path()
        self.assertNotEqual(intro_path, extract_path)
        self.assertTrue(os.path.isfile(intro_path))
        self.assertTrue(os.path.isfile(extract_path))

    def add_test_extract_named_conclusion(self):
        """test the use of an extract named introduction"""

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
        tuto = PubliableContent.objects.get(pk=self.minituto.pk)
        self.assertEqual(Extract.objects.all().count(), 1)
        ccl_path = os.path.join(tuto.get_path(), "conclusion.md")
        extract_path = Extract.objects.get(pk=1).get_path()
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
        tuto = PubliableContent.objects.get(pk=self.minituto.pk)
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
        """Test import of mini tuto."""
        result = self.client.post(
            reverse('zds.tutorial.views.import_tuto'),
            {
                'file': open(
                    os.path.join(
                        settings.SITE_ROOT,
                        'fixtures',
                        'tuto',
                        'securisez-vos-mots-de-passe-avec-lastpass',
                        'securisez-vos-mots-de-passe-avec-lastpass.tuto'),
                    'r'),
                'images': open(
                    os.path.join(
                        settings.SITE_ROOT,
                        'fixtures',
                        'tuto',
                        'securisez-vos-mots-de-passe-avec-lastpass',
                        'images.zip'),
                    'r'),
                'import-tuto': "importer"},
            follow=False)
        self.assertEqual(result.status_code, 302)

        self.assertEqual(PubliableContent.objects.all().count(), 2)

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

        self.assertTrue(PubliableContent.objects.get(pk=self.minituto.pk).image is not None)

        # Delete the image of the minituto.

        response = self.client.post(
            reverse('zds.gallery.views.delete_image'),
            {
                'gallery': self.minituto.gallery.pk,
                'delete_multi': '',
                'items': [image_tutorial.pk]
            },
            follow=True
        )
        self.assertEqual(200, response.status_code)

        # Check if the tutorial is already in database and it doesn't have image.
        self.assertEqual(1, PubliableContent.objects.filter(pk=self.minituto.pk).count())
        self.assertTrue(PubliableContent.objects.get(pk=self.minituto.pk).image is None)

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
        tuto = PubliableContent.objects.filter(pk=self.minituto.pk).first()
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
        tuto = PubliableContent.objects.filter(pk=self.minituto.pk).first()
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
        extract_pk = PubliableContent.objects.get(pk=self.minituto.pk).get_chapter().get_extracts()[0].pk
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
        self.assertEqual(introduction, PubliableContent.objects.filter(pk=self.minituto.pk).first().get_introduction())
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
        sha_draft = PubliableContent.objects.get(pk=self.minituto.pk).sha_draft
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
            PubliableContent.objects.get(pk=self.minituto.pk).sha_beta,
            sha_draft)
        url = PubliableContent.objects.get(pk=self.minituto.pk).get_absolute_url_beta()
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
            PubliableContent.objects.get(pk=self.minituto.pk).sha_beta,
            sha_beta)
        self.assertNotEqual(
            PubliableContent.objects.get(pk=self.minituto.pk).sha_draft,
            sha_beta)
        # update beta
        sha_draft = PubliableContent.objects.get(pk=self.minituto.pk).sha_draft
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
        old_url = url
        url = PubliableContent.objects.get(pk=self.minituto.pk).get_absolute_url_beta()
        # test access to new beta url (get 200) :
        self.assertEqual(
            self.client.get(old_url).status_code,
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
        self.assertEqual(
            self.client.get(old_url).status_code,
            403)

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
            PubliableContent.objects.get(pk=self.minituto.pk).sha_beta,
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
        self.assertEqual(PubliableContent.objects.all().count(), 2)
        tuto = PubliableContent.objects.last()
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
        tuto = PubliableContent.objects.get(pk=self.minituto.pk)
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
        tuto = PubliableContent.objects.get(pk=self.minituto.pk)
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
        tuto = PubliableContent.objects.get(pk=self.minituto.pk)
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
        tuto = PubliableContent.objects.get(pk=self.minituto.pk)
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
        tuto = PubliableContent.objects.get(pk=self.minituto.pk)
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
        tutorial = PubliableContent.objects.get(pk=self.minituto.pk)
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

    def tearDown(self):
        if os.path.isdir(settings.ZDS_APP['tutorial']['repo_path']):
            shutil.rmtree(settings.ZDS_APP['tutorial']['repo_path'])
        if os.path.isdir(settings.ZDS_APP['tutorial']['repo_public_path']):
            shutil.rmtree(settings.ZDS_APP['tutorial']['repo_public_path'])
        if os.path.isdir(settings.ZDS_APP['article']['repo_path']):
            shutil.rmtree(settings.ZDS_APP['article']['repo_path'])
        if os.path.isdir(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)
