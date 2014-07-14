# coding: utf-8

import os
import shutil

from django.conf import settings
from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings

from zds.member.factories import ProfileFactory, StaffProfileFactory
from zds.gallery.factories import GalleryFactory, UserGalleryFactory, ImageFactory
from zds.mp.models import PrivateTopic
from zds.settings import SITE_ROOT
from zds.tutorial.factories import BigTutorialFactory, MiniTutorialFactory, PartFactory, \
    ChapterFactory, NoteFactory, SubCategoryFactory
from zds.gallery.factories import GalleryFactory
from zds.tutorial.models import Note, Tutorial, Validation, Extract, Part, Chapter
from zds.utils.models import SubCategory, Licence, Alert


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
        self.subcat = SubCategoryFactory()

        self.bigtuto = BigTutorialFactory()
        self.bigtuto.authors.add(self.user_author)
        self.bigtuto.gallery = GalleryFactory()
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

        # logout before
        self.client.logout()
        # login with simple member
        self.assertEqual(
            self.client.login(
                username=self.user.username,
                password='hostel77'),
            True)
        
        #add new big tuto
        result = self.client.post(
            reverse('zds.tutorial.views.add_tutorial'),
            {
                'title': u"Introduction à l'algèbre",
                'description': "Perçer les mystère de boole",
                'introduction':"Bienvenue dans le monde binaires",
                'conclusion': "",
                'type': "BIG",
                'subcategory': self.subcat.pk,
            },
            follow=False)
        
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Tutorial.objects.all().count(), 2)
        tuto = Tutorial.objects.last()
        #add part 1
        result = self.client.post(
            reverse('zds.tutorial.views.add_part') + '?tutoriel={}'.format(tuto.pk),
            {
                'title': u"Partie 1",
                'introduction':u"Présentation",
                'conclusion': u"Fin de la présenation",
            },
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Part.objects.filter(tutorial=tuto).count(), 1)
        p1 = Part.objects.filter(tutorial=tuto).last()
        
        #check view offline
        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_part',
                args=[
                    tuto.pk,
                    tuto.slug,
                    p1.pk,
                    p1.slug]),
            follow=True)
        self.assertContains(response=result, text = u"Présentation")
        self.assertContains(response=result, text = u"Fin de la présenation")
        
        #add part 2
        result = self.client.post(
            reverse('zds.tutorial.views.add_part') + '?tutoriel={}'.format(tuto.pk),
            {
                'title': u"Partie 2",
                'introduction': u"Analyse",
                'conclusion': u"Fin de l'analyse",
            },
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Part.objects.filter(tutorial=tuto).count(), 2)
        p2 = Part.objects.filter(tutorial=tuto).last()
        
        #check view offline
        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_part',
                args=[
                    tuto.pk,
                    tuto.slug,
                    p2.pk,
                    p2.slug]),
            follow=True)
        self.assertContains(response=result, text = u"Analyse")
        self.assertContains(response=result, text = u"Fin de l'analyse")

        #add part 3
        result = self.client.post(
            reverse('zds.tutorial.views.add_part') + '?tutoriel={}'.format(tuto.pk),
            {
                'title': u"Partie 2",
                'introduction':"Expérimentation",
                'conclusion': "C'est terminé",
            },
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Part.objects.filter(tutorial=tuto).count(), 3)
        p3 = Part.objects.filter(tutorial=tuto).last()
        
        #check view offline
        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_part',
                args=[
                    tuto.pk,
                    tuto.slug,
                    p3.pk,
                    p3.slug]),
            follow=True)
        self.assertContains(response=result, text = u"Expérimentation")
        self.assertContains(response=result, text = u"C'est terminé")

        #add chapter 1 for part 2
        result = self.client.post(
            reverse('zds.tutorial.views.add_chapter') + '?partie={}'.format(p2.pk),
            {
                'title': u"Chapitre 1",
                'introduction':"Mon premier chapitre",
                'conclusion': "Fin de mon premier chapitre",
            },
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Chapter.objects.filter(part=p1).count(), 0)
        self.assertEqual(Chapter.objects.filter(part=p2).count(), 1)
        self.assertEqual(Chapter.objects.filter(part=p3).count(), 0)
        c1 = Chapter.objects.filter(part=p2).last()
        
        #check view offline
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
        self.assertContains(response=result, text = u"Mon premier chapitre")
        self.assertContains(response=result, text = u"Fin de mon premier chapitre")

        #add chapter 2 for part 2
        result = self.client.post(
            reverse('zds.tutorial.views.add_chapter') + '?partie={}'.format(p2.pk),
            {
                'title': u"Chapitre 2",
                'introduction': u"Mon deuxième chapitre",
                'conclusion':u"Fin de mon deuxième chapitre",
            },
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Chapter.objects.filter(part=p1).count(), 0)
        self.assertEqual(Chapter.objects.filter(part=p2).count(), 2)
        self.assertEqual(Chapter.objects.filter(part=p3).count(), 0)
        c2 = Chapter.objects.filter(part=p2).last()
        
        #check view offline
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
        self.assertContains(response=result, text = u"Mon deuxième chapitre")
        self.assertContains(response=result, text = u"Fin de mon deuxième chapitre")
        
        #add chapter 3 for part 2
        result = self.client.post(
            reverse('zds.tutorial.views.add_chapter') + '?partie={}'.format(p2.pk),
            {
                'title': u"Chapitre 2",
                'introduction': u"Mon troisième chapitre homonyme",
                'conclusion': u"Fin de mon troisième chapitre",
            },
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Chapter.objects.filter(part=p1).count(), 0)
        self.assertEqual(Chapter.objects.filter(part=p2).count(), 3)
        self.assertEqual(Chapter.objects.filter(part=p3).count(), 0)
        c3 = Chapter.objects.filter(part=p2).last()
        
        #check view offline
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
        self.assertContains(response=result, text = u"Mon troisième chapitre homonyme")
        self.assertContains(response=result, text = u"Fin de mon troisième chapitre")
        
        #add chapter 4 for part 1
        result = self.client.post(
            reverse('zds.tutorial.views.add_chapter') + '?partie={}'.format(p1.pk),
            {
                'title': u"Chapitre 1",
                'introduction':"Mon premier chapitre d'une autre partie",
                'conclusion': "",
            },
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Chapter.objects.filter(part=p1).count(), 1)
        self.assertEqual(Chapter.objects.filter(part=p2).count(), 3)
        self.assertEqual(Chapter.objects.filter(part=p3).count(), 0)
        c4 = Chapter.objects.filter(part=p1).last()
        
        #check view offline
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
        self.assertContains(response=result, text = u"Mon premier chapitre d'une autre partie")
        
        #edit part 2
        result = self.client.post(
            reverse('zds.tutorial.views.edit_part') + '?partie={}'.format(p2.pk),
            {
                'title': u"Partie 2 : edition de titre",
                'introduction': u"Expérimentation : edition d'introduction",
                'conclusion': u"C'est terminé : edition de conlusion",
            },
            follow=True)
        self.assertContains(response=result, text = u"Partie 2 : edition de titre")
        self.assertContains(response=result, text = u"Expérimentation : edition d'introduction")
        self.assertContains(response=result, text = u"C'est terminé : edition de conlusion")
        self.assertEqual(Part.objects.filter(tutorial=tuto).count(), 3)
        
        #edit chapter 3
        result = self.client.post(
            reverse('zds.tutorial.views.edit_chapter') + '?chapitre={}'.format(c3.pk),
            {
                'title': u"Chapitre 3 : edition de titre",
                'introduction': u"Edition d'introduction",
                'conclusion': u"Edition de conlusion",
            },
            follow=True)
        self.assertContains(response=result, text = u"Chapitre 3 : edition de titre")
        self.assertContains(response=result, text = u"Edition d'introduction")
        self.assertContains(response=result, text = u"Edition de conlusion")
        self.assertEqual(Chapter.objects.filter(part=p2.pk).count(), 3)
        
        #edit part 2
        result = self.client.post(
            reverse('zds.tutorial.views.edit_part') + '?partie={}'.format(p2.pk),
            {
                'title': u"Partie 2 : seconde edition de titre",
                'introduction': u"Expérimentation : seconde edition d'introduction",
                'conclusion': u"C'est terminé : seconde edition de conlusion",
            },
            follow=True)
        self.assertContains(response=result, text = u"Partie 2 : seconde edition de titre")
        self.assertContains(response=result, text = u"Expérimentation : seconde edition d'introduction")
        self.assertContains(response=result, text = u"C'est terminé : seconde edition de conlusion")
        self.assertEqual(Part.objects.filter(tutorial=tuto).count(), 3)
        
        #edit chapter 2
        result = self.client.post(
            reverse('zds.tutorial.views.edit_chapter') + '?chapitre={}'.format(c2.pk),
            {
                'title': u"Chapitre 2 : edition de titre",
                'introduction': u"Edition d'introduction",
                'conclusion': u"Edition de conlusion",
            },
            follow=True)
        self.assertContains(response=result, text = u"Chapitre 2 : edition de titre")
        self.assertContains(response=result, text = u"Edition d'introduction")
        self.assertContains(response=result, text = u"Edition de conlusion")
        self.assertEqual(Chapter.objects.filter(part=p2.pk).count(), 3)
        
        #move chapter 1 against 2
        result = self.client.post(
            reverse('zds.tutorial.views.modify_chapter'),
            {
                'chapter': c1.pk,
                'move_target': c2.position_in_part,
            },
            follow=True)
        #move part 1 against 2
        result = self.client.post(
            reverse('zds.tutorial.views.modify_part'),
            {
                'part': p1.pk,
                'move_target': p2.position_in_tutorial,
            },
            follow=True)
        self.assertEqual(Chapter.objects.filter(part__tutorial=tuto.pk).count(), 4)

        #delete part 1
        result = self.client.post(
            reverse('zds.tutorial.views.modify_part'),
            {
                'part': p1.pk,
                'delete': "OK",
            },
            follow=True)
        #delete chapter 3
        result = self.client.post(
            reverse('zds.tutorial.views.modify_chapter'),
            {
                'chapter': c3.pk,
                'delete': "OK",
            },
            follow=True)
        self.assertEqual(Chapter.objects.filter(part__tutorial=tuto.pk).count(), 2)
        self.assertEqual(Part.objects.filter(tutorial=tuto.pk).count(), 2)

    def test_available_tuto(self):
        """ Test that all page of big tutorial is available"""
        parts = self.bigtuto.get_parts()
        for part in parts:
            result = self.client.get(reverse(
                                        'zds.tutorial.views.view_part_online',
                                        args=[
                                            self.bigtuto.pk,
                                            self.bigtuto.slug,
                                            part.pk,
                                            part.slug]),
                                    follow=True)
            self.assertEqual(result.status_code, 200)
            result = self.client.get(reverse(
                                        'zds.tutorial.views.view_part',
                                        args=[
                                            self.bigtuto.pk,
                                            self.bigtuto.slug,
                                            part.pk,
                                            part.slug]),
                                    follow=True)
            self.assertEqual(result.status_code, 200)
            chapters = part.get_chapters()
            for chapter in chapters:
                result = self.client.get(reverse(
                                            'zds.tutorial.views.view_chapter_online',
                                            args=[
                                                self.bigtuto.pk,
                                                self.bigtuto.slug,
                                                part.pk,
                                                part.slug,
                                                chapter.pk,
                                                chapter.slug]),
                                        follow=True)
                self.assertEqual(result.status_code, 200)
                result = self.client.get(reverse(
                                            'zds.tutorial.views.view_chapter',
                                            args=[
                                                self.bigtuto.pk,
                                                self.bigtuto.slug,
                                                part.pk,
                                                part.slug,
                                                chapter.pk,
                                                chapter.slug]),
                                        follow=True)
                self.assertEqual(result.status_code, 200)

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
        user_gallery = UserGalleryFactory(user=self.user_author, gallery=self.bigtuto.gallery)

        self.bigtuto.image = image_tutorial
        self.bigtuto.save()

        self.assertTrue(Tutorial.objects.get(pk=self.bigtuto.pk).image != None)

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
        self.assertEqual(1, Tutorial.objects.filter(pk=self.bigtuto.pk).count())
        self.assertTrue(Tutorial.objects.get(pk=self.bigtuto.pk).image == None)

    def test_workflow_beta_tuto(self) :
        "Ensure the behavior of the beta version of tutorials"

        # logout before
        self.client.logout()
        # first, login with author :
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)
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
        # test access for random user (get 200)
        self.assertEqual(
            self.client.login(
                username=self.user.username,
                password='hostel77'),
            True)
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
            reverse( 'zds.tutorial.views.add_extract') +
            '?chapitre={0}'.format(
                self.chapter2_1.pk),

            {
            'title' : "Introduction",
            'text' : u"Le contenu de l'extrait"
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
        old_url = url
        url = Tutorial.objects.get(pk=self.bigtuto.pk).get_absolute_url_beta()
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

        self.subcat = SubCategoryFactory()

        self.minituto = MiniTutorialFactory()
        self.minituto.authors.add(self.user_author)
        self.minituto.gallery = GalleryFactory()
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
        self.minituto = Tutorial.objects.get(pk=self.minituto.pk)
        self.assertEqual(self.minituto.on_line(), True)
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
        user_gallery = UserGalleryFactory(user=self.user_author, gallery=self.minituto.gallery)

        self.minituto.image = image_tutorial
        self.minituto.save()

        self.assertTrue(Tutorial.objects.get(pk=self.minituto.pk).image != None)

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
        self.assertEqual(1, Tutorial.objects.filter(pk=self.minituto.pk).count())
        self.assertTrue(Tutorial.objects.get(pk=self.minituto.pk).image == None)

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
        #edit the tuto without slug change
        response = self.client.post(
                reverse('zds.tutorial.views.edit_tutorial') + "?tutoriel={0}".format(self.minituto.pk),
                {
                    'title': self.minituto.title,
                    'description': "nouvelle description",
                    'subcategory': [sub.pk],
                    'introduction': self.minituto.get_introduction(),
                    'conclusion': self.minituto.get_conclusion(),
                },
                follow=False
        )
        self.assertEqual(302, response.status_code)
        tuto = Tutorial.objects.filter(pk=self.minituto.pk).first()
        self.assertEqual(tuto.title, self.minituto.title)
        self.assertEqual(tuto.description, "nouvelle description")
        #edit tuto with a slug change
        (introduction, conclusion) = (self.minituto.get_introduction(), self.minituto.get_conclusion())
        self.client.post(
                reverse('zds.tutorial.views.edit_tutorial') + "?tutoriel={0}".format(self.minituto.pk),
                {
                    'title': "nouveau titre pour nouveau slug",
                    'description': "nouvelle description",
                    'subcategory': [sub.pk],
                    'introduction': self.minituto.get_introduction(),
                    'conclusion': self.minituto.get_conclusion(),
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
        (introduction, conclusion) = (self.minituto.get_introduction(), self.minituto.get_conclusion())
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
    
    def test_workflow_beta_tuto(self) :
        "Ensure the behavior of the beta version of tutorials"

        # logout before
        self.client.logout()
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
        
        # then modify tutorial
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)
        result = self.client.post(
            reverse( 'zds.tutorial.views.add_extract') +
            '?chapitre={0}'.format(
                self.chapter.pk),

            {
            'title' : "Introduction",
            'text' : u"Le contenu de l'extrait"
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
        old_url = url
        url = Tutorial.objects.get(pk=self.minituto.pk).get_absolute_url_beta()
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

        # logout before
        self.client.logout()
        # login with simple member
        self.assertEqual(
            self.client.login(
                username=self.user.username,
                password='hostel77'),
            True)
        
        #add new mini tuto
        result = self.client.post(
            reverse('zds.tutorial.views.add_tutorial'),
            {
                'title': u"Introduction à l'algèbre",
                'description': "Perçer les mystère de boole",
                'introduction':"Bienvenue dans le monde binaires",
                'conclusion': "",
                'type': "MINI",
                'subcategory': self.subcat.pk,
            },
            follow=False)
        
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Tutorial.objects.all().count(), 2)
        tuto = Tutorial.objects.last()
        chapter = Chapter.objects.filter(tutorial__pk=tuto.pk).first()
        
        #add extract 1
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

        #check view offline
        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_tutorial',
                args=[
                    tuto.pk,
                    tuto.slug]),
            follow=True)
        self.assertContains(response=result, text = u"Extrait 1")
        self.assertContains(response=result, text = u"Introduisons notre premier extrait")
        
        #add extract 2
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

        #check view offline
        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_tutorial',
                args=[
                    tuto.pk,
                    tuto.slug]),
            follow=True)
        self.assertContains(response=result, text = u"Extrait 2")
        self.assertContains(response=result, text = u"Introduisons notre deuxième extrait")

        #add extract 3
        result = self.client.post(
            reverse('zds.tutorial.views.add_extract') + '?chapitre={}'.format(chapter.pk),
            {
                'title': u"Extrait 3",
                'text': u"Introduisons notre troisième extrait",
            },
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Extract.objects.filter(chapter=chapter).count(), 3)
        e3 = Extract.objects.filter(chapter=chapter).last()

        #check view offline
        result = self.client.get(
            reverse(
                'zds.tutorial.views.view_tutorial',
                args=[
                    tuto.pk,
                    tuto.slug]),
            follow=True)
        self.assertContains(response=result, text = u"Extrait 3")
        self.assertContains(response=result, text = u"Introduisons notre troisième extrait")
        
        #edit extract 2
        result = self.client.post(
            reverse('zds.tutorial.views.edit_extract') + '?extrait={}'.format(e2.pk),
            {
                'title': u"Extrait 2 : edition de titre",
                'text': u"Edition d'introduction",
            },
            follow=True)
        self.assertEqual(result.status_code, 200)
        self.assertContains(response=result, text = u"Extrait 2 : edition de titre")
        self.assertContains(response=result, text = u"Edition d'introduction")
        self.assertEqual(Extract.objects.filter(chapter__tutorial=tuto).count(), 3)
        
        #move extract 1 against 2
        result = self.client.post(
            reverse('zds.tutorial.views.modify_extract'),
            {
                'extract': e1.pk,
                'move_target': e2.position_in_chapter,
            },
            follow=True)

        #delete extract 1
        result = self.client.post(
            reverse('zds.tutorial.views.modify_extract'),
            {
                'extract': e1.pk,
                'delete': "OK",
            },
            follow=True)

        self.assertEqual(Extract.objects.filter(chapter__tutorial=tuto).count(), 2)

    def tearDown(self):
        if os.path.isdir(settings.REPO_PATH):
            shutil.rmtree(settings.REPO_PATH)
        if os.path.isdir(settings.REPO_PATH_PROD):
            shutil.rmtree(settings.REPO_PATH_PROD)
        if os.path.isdir(settings.REPO_ARTICLE_PATH):
            shutil.rmtree(settings.REPO_ARTICLE_PATH)
        if os.path.isdir(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)
