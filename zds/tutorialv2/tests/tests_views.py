# coding: utf-8
from django.contrib.auth.models import Group

import os
import shutil
import tempfile
import zipfile

from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings
from django.core.urlresolvers import reverse
from django.contrib import messages

from zds.gallery.models import GALLERY_WRITE, UserGallery
from zds.settings import BASE_DIR
from zds.member.factories import ProfileFactory, StaffProfileFactory
from zds.tutorialv2.factories import PublishableContentFactory, ContainerFactory, ExtractFactory, LicenceFactory, \
    SubCategoryFactory, PublishedContentFactory
from zds.tutorialv2.models.models_database import PublishableContent, Validation, PublishedContent, ContentReaction
from zds.gallery.factories import GalleryFactory
from zds.forum.factories import ForumFactory, CategoryFactory
from zds.forum.models import Topic, Post
from zds.mp.models import PrivateTopic
from django.utils.encoding import smart_text
from zds.utils.models import HelpWriting, CommentDislike, CommentLike, Alert
from zds.utils.factories import HelpWritingFactory


overrided_zds_app = settings.ZDS_APP
overrided_zds_app['content']['repo_private_path'] = os.path.join(BASE_DIR, 'contents-private-test')
overrided_zds_app['content']['repo_public_path'] = os.path.join(BASE_DIR, 'contents-public-test')


@override_settings(MEDIA_ROOT=os.path.join(BASE_DIR, 'media-test'))
@override_settings(ZDS_APP=overrided_zds_app)
class ContentTests(TestCase):
    def setUp(self):
        self.staff = StaffProfileFactory().user

        settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
        self.mas = ProfileFactory().user
        settings.ZDS_APP['member']['bot_account'] = self.mas.username

        self.licence = LicenceFactory()
        self.subcategory = SubCategoryFactory()

        self.user_author = ProfileFactory().user
        self.user_staff = StaffProfileFactory().user
        self.user_guest = ProfileFactory().user

        self.tuto = PublishableContentFactory(type='TUTORIAL')
        self.tuto.authors.add(self.user_author)
        self.tuto.gallery = GalleryFactory()
        self.tuto.licence = self.licence
        self.tuto.subcategory.add(self.subcategory)
        self.tuto.save()

        self.beta_forum = ForumFactory(
            pk=settings.ZDS_APP['forum']['beta_forum_id'],
            category=CategoryFactory(position=1),
            position_in_category=1)  # ensure that the forum, for the beta versions, is created

        self.tuto_draft = self.tuto.load_version()
        self.part1 = ContainerFactory(parent=self.tuto_draft, db_object=self.tuto)
        self.chapter1 = ContainerFactory(parent=self.part1, db_object=self.tuto)

        self.extract1 = ExtractFactory(container=self.chapter1, db_object=self.tuto)
        bot = Group(name=settings.ZDS_APP["member"]["bot_group"])
        bot.save()

    def test_ensure_access(self):
        """General access test for author, user, guest and staff"""

        # login with author
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)

        tuto = PublishableContent.objects.get(pk=self.tuto.pk)

        # check access for author (get 200, for content, part, chapter)
        result = self.client.get(
            reverse('content:view', args=[tuto.pk, tuto.slug]),
            follow=False)
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse('content:view-container',
                    kwargs={
                        'pk': tuto.pk,
                        'slug': tuto.slug,
                        'container_slug': self.part1.slug
                    }),
            follow=False)
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse('content:view-container',
                    kwargs={
                        'pk': tuto.pk,
                        'slug': tuto.slug,
                        'parent_container_slug': self.part1.slug,
                        'container_slug': self.chapter1.slug
                    }),
            follow=False)
        self.assertEqual(result.status_code, 200)

        self.client.logout()

        # check access for public (get 302, for content, part, chapter)
        result = self.client.get(
            reverse('content:view', args=[tuto.pk, tuto.slug]),
            follow=False)
        self.assertEqual(result.status_code, 302)

        result = self.client.get(
            reverse('content:view-container',
                    kwargs={
                        'pk': tuto.pk,
                        'slug': tuto.slug,
                        'container_slug': self.part1.slug
                    }),
            follow=False)
        self.assertEqual(result.status_code, 302)

        result = self.client.get(
            reverse('content:view-container',
                    kwargs={
                        'pk': tuto.pk,
                        'slug': tuto.slug,
                        'parent_container_slug': self.part1.slug,
                        'container_slug': self.chapter1.slug
                    }),
            follow=False)
        self.assertEqual(result.status_code, 302)

        # login with guest
        self.assertEqual(
            self.client.login(
                username=self.user_guest.username,
                password='hostel77'),
            True)

        tuto = PublishableContent.objects.get(pk=self.tuto.pk)

        # check access for guest (get 403 for content, part and chapter, since he is not part of the authors)
        result = self.client.get(
            reverse('content:view', args=[tuto.pk, tuto.slug]),
            follow=False)
        self.assertEqual(result.status_code, 403)

        result = self.client.get(
            reverse('content:view-container',
                    kwargs={
                        'pk': tuto.pk,
                        'slug': tuto.slug,
                        'container_slug': self.part1.slug
                    }),
            follow=False)
        self.assertEqual(result.status_code, 403)

        result = self.client.get(
            reverse('content:view-container',
                    kwargs={
                        'pk': tuto.pk,
                        'slug': tuto.slug,
                        'parent_container_slug': self.part1.slug,
                        'container_slug': self.chapter1.slug
                    }),
            follow=False)
        self.assertEqual(result.status_code, 403)

        # login with staff
        self.assertEqual(
            self.client.login(
                username=self.user_staff.username,
                password='hostel77'),
            True)

        tuto = PublishableContent.objects.get(pk=self.tuto.pk)

        # check access for staff (get 200 for content, part and chapter)
        result = self.client.get(
            reverse('content:view', args=[tuto.pk, tuto.slug]),
            follow=False)
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse('content:view-container',
                    kwargs={
                        'pk': tuto.pk,
                        'slug': tuto.slug,
                        'container_slug': self.part1.slug
                    }),
            follow=False)
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse('content:view-container',
                    kwargs={
                        'pk': tuto.pk,
                        'slug': tuto.slug,
                        'parent_container_slug': self.part1.slug,
                        'container_slug': self.chapter1.slug
                    }),
            follow=False)
        self.assertEqual(result.status_code, 200)

    def test_basic_tutorial_workflow(self):
        """General test on the basic workflow of a tutorial: creation, edition, deletion for the author"""

        # login with author
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)

        # create tutorial
        intro = u'une intro'
        conclusion = u'une conclusion'
        description = u'une description'
        title = u'un titre'
        random = u'un truc à la rien à voir'

        result = self.client.post(
            reverse('content:create'),
            {
                'title': title,
                'description': description,
                'introduction': intro,
                'conclusion': conclusion,
                'type': u'TUTORIAL',
                'licence': self.licence.pk,
                'subcategory': self.subcategory.pk,
            },
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(PublishableContent.objects.all().count(), 2)

        tuto = PublishableContent.objects.last()
        pk = tuto.pk
        slug = tuto.slug
        versioned = tuto.load_version()

        # access to tutorial
        result = self.client.get(
            reverse('content:edit', args=[pk, slug]),
            follow=False)
        self.assertEqual(result.status_code, 200)

        # edit tutorial:
        new_licence = LicenceFactory()

        result = self.client.post(
            reverse('content:edit', args=[pk, slug]),
            {
                'title': random,
                'description': random,
                'introduction': random,
                'conclusion': random,
                'type': u'TUTORIAL',
                'licence': new_licence.pk,
                'subcategory': self.subcategory.pk,
                'last_hash': versioned.compute_hash()
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        tuto = PublishableContent.objects.get(pk=pk)
        self.assertEqual(tuto.title, random)
        self.assertEqual(tuto.description, random)
        self.assertEqual(tuto.licence.pk, new_licence.pk)
        versioned = tuto.load_version()
        self.assertEqual(versioned.get_introduction(), random)
        self.assertEqual(versioned.get_conclusion(), random)
        self.assertEqual(versioned.description, random)
        self.assertEqual(versioned.licence.pk, new_licence.pk)
        self.assertNotEqual(versioned.slug, slug)

        slug = tuto.slug  # make the title change also change the slug !!

        # create container:
        result = self.client.post(
            reverse('content:create-container', args=[pk, slug]),
            {
                'title': title,
                'introduction': intro,
                'conclusion': conclusion
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        versioned = PublishableContent.objects.get(pk=pk).load_version()
        self.assertEqual(len(versioned.children), 1)  # ok, the container is created
        container = versioned.children[0]
        self.assertEqual(container.title, title)
        self.assertEqual(container.get_introduction(), intro)
        self.assertEqual(container.get_conclusion(), conclusion)

        # access container:
        result = self.client.get(
            reverse('content:view-container', kwargs={'pk': pk, 'slug': slug, 'container_slug': container.slug}),
            follow=False)
        self.assertEqual(result.status_code, 200)

        # edit container:
        old_slug_container = container.slug
        result = self.client.post(
            reverse('content:edit-container', kwargs={'pk': pk, 'slug': slug, 'container_slug': container.slug}),
            {
                'title': random,
                'introduction': random,
                'conclusion': random,
                'last_hash': container.compute_hash()
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        versioned = PublishableContent.objects.get(pk=pk).load_version()
        container = versioned.children[0]
        self.assertEqual(container.title, random)
        self.assertEqual(container.get_introduction(), random)
        self.assertEqual(container.get_conclusion(), random)
        self.assertNotEqual(container.slug, old_slug_container)

        # add a subcontainer
        result = self.client.post(
            reverse('content:create-container', kwargs={'pk': pk, 'slug': slug, 'container_slug': container.slug}),
            {
                'title': title,
                'introduction': intro,
                'conclusion': conclusion
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        versioned = PublishableContent.objects.get(pk=pk).load_version()
        self.assertEqual(len(versioned.children[0].children), 1)  # the subcontainer is created
        subcontainer = versioned.children[0].children[0]
        self.assertEqual(subcontainer.title, title)
        self.assertEqual(subcontainer.get_introduction(), intro)
        self.assertEqual(subcontainer.get_conclusion(), conclusion)

        # access the subcontainer
        result = self.client.get(
            reverse('content:view-container',
                    kwargs={
                        'pk': pk,
                        'slug': slug,
                        'parent_container_slug': container.slug,
                        'container_slug': subcontainer.slug
                    }),
            follow=False)
        self.assertEqual(result.status_code, 200)

        # edit subcontainer:
        old_slug_subcontainer = subcontainer.slug
        result = self.client.post(
            reverse('content:edit-container',
                    kwargs={
                        'pk': pk,
                        'slug': slug,
                        'parent_container_slug': container.slug,
                        'container_slug': subcontainer.slug
                    }),
            {
                'title': random,
                'introduction': random,
                'conclusion': random,
                'last_hash': subcontainer.compute_hash()
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        versioned = PublishableContent.objects.get(pk=pk).load_version()
        subcontainer = versioned.children[0].children[0]
        self.assertEqual(subcontainer.title, random)
        self.assertEqual(subcontainer.get_introduction(), random)
        self.assertEqual(subcontainer.get_conclusion(), random)
        self.assertNotEqual(subcontainer.slug, old_slug_subcontainer)

        # add extract to subcontainer:
        result = self.client.post(
            reverse('content:create-extract',
                    kwargs={
                        'pk': pk,
                        'slug': slug,
                        'parent_container_slug': container.slug,
                        'container_slug': subcontainer.slug
                    }),
            {
                'title': title,
                'text': description
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        versioned = PublishableContent.objects.get(pk=pk).load_version()
        self.assertEqual(len(versioned.children[0].children[0].children), 1)  # the extract is created
        extract = versioned.children[0].children[0].children[0]
        self.assertEqual(extract.title, title)
        self.assertEqual(extract.get_text(), description)

        # access the subcontainer again (with the extract)
        result = self.client.get(
            reverse('content:view-container',
                    kwargs={
                        'pk': pk,
                        'slug': slug,
                        'parent_container_slug': container.slug,
                        'container_slug': subcontainer.slug
                    }),
            follow=False)
        self.assertEqual(result.status_code, 200)

        # edit extract:
        old_slug_extract = extract.slug
        result = self.client.post(
            reverse('content:edit-extract',
                    kwargs={
                        'pk': pk,
                        'slug': slug,
                        'parent_container_slug': container.slug,
                        'container_slug': subcontainer.slug,
                        'extract_slug': extract.slug
                    }),
            {
                'title': random,
                'text': random,
                'last_hash': extract.compute_hash()
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        versioned = PublishableContent.objects.get(pk=pk).load_version()
        extract = versioned.children[0].children[0].children[0]
        self.assertEqual(extract.title, random)
        self.assertEqual(extract.get_text(), random)
        self.assertNotEqual(old_slug_extract, extract.slug)

        # then, delete extract:
        result = self.client.get(
            reverse('content:delete',
                    kwargs={
                        'pk': pk,
                        'slug': slug,
                        'parent_container_slug': container.slug,
                        'container_slug': subcontainer.slug,
                        'object_slug': extract.slug
                    }),
            follow=False)
        self.assertEqual(result.status_code, 405)  # it is not working with get !

        versioned = PublishableContent.objects.get(pk=pk).load_version()
        self.assertEqual(len(versioned.children[0].children[0].children), 1)  # and the extract still exists

        result = self.client.post(
            reverse('content:delete',
                    kwargs={
                        'pk': pk,
                        'slug': slug,
                        'parent_container_slug': container.slug,
                        'container_slug': subcontainer.slug,
                        'object_slug': extract.slug
                    }),
            follow=False)
        self.assertEqual(result.status_code, 302)

        versioned = PublishableContent.objects.get(pk=pk).load_version()
        self.assertEqual(len(versioned.children[0].children[0].children), 0)  # extract was deleted
        self.assertFalse(os.path.exists(extract.get_path()))  # and physically deleted as well

        # delete subcontainer:
        result = self.client.post(
            reverse('content:delete',
                    kwargs={
                        'pk': pk,
                        'slug': slug,
                        'container_slug': container.slug,
                        'object_slug': subcontainer.slug
                    }),
            follow=False)
        self.assertEqual(result.status_code, 302)

        versioned = PublishableContent.objects.get(pk=pk).load_version()
        self.assertEqual(len(versioned.children[0].children), 0)  # subcontainer was deleted
        self.assertFalse(os.path.exists(subcontainer.get_path()))

        # delete container:
        result = self.client.post(
            reverse('content:delete',
                    kwargs={
                        'pk': pk,
                        'slug': slug,
                        'object_slug': container.slug
                    }),
            follow=False)
        self.assertEqual(result.status_code, 302)

        versioned = PublishableContent.objects.get(pk=pk).load_version()
        self.assertEqual(len(versioned.children), 0)  # container was deleted
        self.assertFalse(os.path.exists(container.get_path()))

        # and delete tutorial itself
        result = self.client.post(
            reverse('content:delete', args=[pk, slug]),
            follow=False)
        self.assertEqual(result.status_code, 302)

        self.assertFalse(os.path.isfile(versioned.get_path()))  # deletion get right ;)

    def test_beta_workflow(self):
        """Test beta workflow (access and update)"""

        # login with guest and test the non-access
        self.assertEqual(
            self.client.login(
                username=self.user_guest.username,
                password='hostel77'),
            True)

        result = self.client.get(
            reverse('content:view', args=[self.tuto.pk, self.tuto.slug]),
            follow=False)
        self.assertEqual(result.status_code, 403)  # (get 403 since he is not part of the authors)

        # login with author
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)

        # activ beta:
        tuto = PublishableContent.objects.get(pk=self.tuto.pk)
        current_sha_beta = tuto.sha_draft
        result = self.client.post(
            reverse('content:set-beta', kwargs={'pk': tuto.pk, 'slug': tuto.slug}),
            {
                'version': current_sha_beta
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        # check if there is a new topic and a pm corresponding to the tutorial in beta
        self.assertEqual(Topic.objects.filter(forum=self.beta_forum).count(), 1)
        self.assertTrue(PublishableContent.objects.get(pk=self.tuto.pk).beta_topic is not None)
        self.assertEqual(PrivateTopic.objects.filter(author=self.user_author).count(), 1)

        beta_topic = PublishableContent.objects.get(pk=self.tuto.pk).beta_topic
        self.assertEqual(Post.objects.filter(topic=beta_topic).count(), 1)
        self.assertEqual(beta_topic.tags.count(), 1)
        self.assertEqual(beta_topic.tags.first().title, smart_text(self.subcategory.title).lower()[:20])
        # test access for public
        self.client.logout()

        result = self.client.get(
            reverse('content:view', args=[self.tuto.pk, self.tuto.slug]) + '?version=' + current_sha_beta,
            follow=False)
        self.assertEqual(result.status_code, 302)  # (get 302: no access to beta for public)

        # test access for guest;
        self.assertEqual(
            self.client.login(
                username=self.user_guest.username,
                password='hostel77'),
            True)

        # get 200 everywhere :)
        result = self.client.get(
            reverse('content:view', args=[tuto.pk, tuto.slug]) + '?version=' + current_sha_beta,
            follow=False)
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse('content:view-container',
                    kwargs={
                        'pk': tuto.pk,
                        'slug': tuto.slug,
                        'container_slug': self.part1.slug
                    }) + '?version=' + current_sha_beta,
            follow=False)
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse('content:view-container',
                    kwargs={
                        'pk': tuto.pk,
                        'slug': tuto.slug,
                        'parent_container_slug': self.part1.slug,
                        'container_slug': self.chapter1.slug
                    }) + '?version=' + current_sha_beta,
            follow=False)
        self.assertEqual(result.status_code, 200)

        # change beta version
        self.client.logout()
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)

        result = self.client.post(
            reverse('content:edit-container',
                    kwargs={
                        'pk': tuto.pk,
                        'slug': tuto.slug,
                        'container_slug': self.part1.slug
                    }),
            {
                'title': u'Un autre titre',
                'introduction': u'Introduire la chose',
                'conclusion': u'Et terminer sur un truc bien',
                'last_hash': self.part1.compute_hash()
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        tuto = PublishableContent.objects.get(pk=tuto.pk)
        self.assertNotEqual(current_sha_beta, tuto.sha_draft)

        # change beta:
        old_sha_beta = current_sha_beta
        current_sha_beta = tuto.sha_draft
        result = self.client.post(
            reverse('content:set-beta', kwargs={'pk': tuto.pk, 'slug': tuto.slug}),
            {
                'version': current_sha_beta
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        tuto = PublishableContent.objects.get(pk=tuto.pk)
        self.assertEqual(tuto.sha_beta, current_sha_beta)

        self.assertEqual(Post.objects.filter(topic=beta_topic).count(), 2)  # a new message was added !

        # then test for guest
        self.client.logout()
        self.assertEqual(
            self.client.login(
                username=self.user_guest.username,
                password='hostel77'),
            True)

        result = self.client.get(
            reverse('content:view', args=[tuto.pk, tuto.slug]) + '?version=' + old_sha_beta,
            follow=False)
        self.assertEqual(result.status_code, 403)  # no access using the old version

        result = self.client.get(
            reverse('content:view', args=[tuto.pk, tuto.slug]) + '?version=' + current_sha_beta,
            follow=False)
        self.assertEqual(result.status_code, 200)  # ok for the new version

        # inactive beta
        self.client.logout()
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)

        result = self.client.post(
            reverse('content:inactive-beta', kwargs={'pk': tuto.pk, 'slug': tuto.slug}),
            {
                'version': current_sha_beta
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        self.assertEqual(Post.objects.filter(topic=beta_topic).count(), 3)  # a new message was added !
        self.assertTrue(Topic.objects.get(pk=beta_topic.pk).is_locked)  # beta was inactived, so topic is locked !

        # then test for guest
        self.client.logout()
        self.assertEqual(
            self.client.login(
                username=self.user_guest.username,
                password='hostel77'),
            True)

        result = self.client.get(
            reverse('content:view', args=[tuto.pk, tuto.slug]) + '?version=' + current_sha_beta,
            follow=False)
        self.assertEqual(result.status_code, 403)  # no access anymore

        # reactive beta
        self.client.logout()
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)

        result = self.client.post(
            reverse('content:set-beta', kwargs={'pk': tuto.pk, 'slug': tuto.slug}),
            {
                'version': old_sha_beta  # with a different version than the draft one
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        tuto = PublishableContent.objects.get(pk=tuto.pk)
        self.assertEqual(tuto.sha_beta, old_sha_beta)

        self.assertEqual(Post.objects.filter(topic=beta_topic).count(), 4)  # a new message was added !
        self.assertFalse(Topic.objects.get(pk=beta_topic.pk).is_locked)  # not locked anymore

        # then test for guest
        self.client.logout()
        self.assertEqual(
            self.client.login(
                username=self.user_guest.username,
                password='hostel77'),
            True)

        result = self.client.get(
            reverse('content:view', args=[tuto.pk, tuto.slug]) + '?version=' + tuto.sha_draft,
            follow=False)
        self.assertEqual(result.status_code, 403)  # no access on the non-beta version (of course)

        result = self.client.get(
            reverse('content:view', args=[tuto.pk, tuto.slug]) + '?version=' + old_sha_beta,
            follow=False)
        self.assertEqual(result.status_code, 200)  # access granted

    def test_history_navigation(self):
        """ensure that, if the title (and so the slug) of the content change, its content remain accessible"""
        # login with author
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)

        tuto = PublishableContent.objects.get(pk=self.tuto.pk)
        versioned = tuto.load_version()

        # check access
        result = self.client.get(
            reverse('content:view', args=[tuto.pk, tuto.slug]),
            follow=False)
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse('content:view-container',
                    kwargs={
                        'pk': tuto.pk,
                        'slug': tuto.slug,
                        'container_slug': self.part1.slug
                    }),
            follow=False)
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse('content:view-container',
                    kwargs={
                        'pk': tuto.pk,
                        'slug': tuto.slug,
                        'parent_container_slug': self.part1.slug,
                        'container_slug': self.chapter1.slug
                    }),
            follow=False)
        self.assertEqual(result.status_code, 200)

        # edit tutorial:
        old_slug_tuto = tuto.slug
        version_1 = tuto.sha_draft  # "version 1" is the one before any change

        new_licence = LicenceFactory()
        random = 'Pâques, c\'est bientôt?'

        result = self.client.post(
            reverse('content:edit', args=[tuto.pk, tuto.slug]),
            {
                'title': random,
                'description': random,
                'introduction': random,
                'conclusion': random,
                'type': u'TUTORIAL',
                'licence': new_licence.pk,
                'subcategory': self.subcategory.pk,
                'last_hash': versioned.compute_hash()
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        tuto = PublishableContent.objects.get(pk=self.tuto.pk)
        version_2 = tuto.sha_draft  # "version 2" is the one with the different slug for the tutorial
        self.assertNotEqual(tuto.slug, old_slug_tuto)

        # check access using old slug and no version
        result = self.client.get(
            reverse('content:view', args=[tuto.pk, old_slug_tuto]),
            follow=False)
        self.assertEqual(result.status_code, 404)  # it is not possible, so get 404

        result = self.client.get(
            reverse('content:view-container',
                    kwargs={
                        'pk': tuto.pk,
                        'slug': old_slug_tuto,
                        'container_slug': self.part1.slug
                    }),
            follow=False)
        self.assertEqual(result.status_code, 404)

        result = self.client.get(
            reverse('content:view-container',
                    kwargs={
                        'pk': tuto.pk,
                        'slug': old_slug_tuto,
                        'parent_container_slug': self.part1.slug,
                        'container_slug': self.chapter1.slug
                    }),
            follow=False)
        self.assertEqual(result.status_code, 404)

        # check access with old slug and version
        result = self.client.get(
            reverse('content:view', args=[tuto.pk, old_slug_tuto]) + '?version=' + version_1,
            follow=False)
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse('content:view-container',
                    kwargs={
                        'pk': tuto.pk,
                        'slug': old_slug_tuto,
                        'container_slug': self.part1.slug
                    }) + '?version=' + version_1,
            follow=False)
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse('content:view-container',
                    kwargs={
                        'pk': tuto.pk,
                        'slug': old_slug_tuto,
                        'parent_container_slug': self.part1.slug,
                        'container_slug': self.chapter1.slug
                    }) + '?version=' + version_1,
            follow=False)
        self.assertEqual(result.status_code, 200)

        # edit container:
        old_slug_part = self.part1.slug
        part1 = tuto.load_version().children[0]
        result = self.client.post(
            reverse('content:edit-container', kwargs={
                'pk': tuto.pk,
                'slug': tuto.slug,
                'container_slug': self.part1.slug
            }),
            {
                'title': random,
                'introduction': random,
                'conclusion': random,
                'last_hash': part1.compute_hash()
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        tuto = PublishableContent.objects.get(pk=self.tuto.pk)
        version_3 = tuto.sha_draft  # "version 3" is the one with the modified part
        versioned = tuto.load_version()
        current_slug_part = versioned.children[0].slug

        # we can still access to the container using old slug !
        result = self.client.get(
            reverse('content:view-container',
                    kwargs={
                        'pk': tuto.pk,
                        'slug': tuto.slug,
                        'container_slug': old_slug_part
                    }) + '?version=' + version_2,
            follow=False)
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse('content:view-container',
                    kwargs={
                        'pk': tuto.pk,
                        'slug': tuto.slug,
                        'parent_container_slug': old_slug_part,
                        'container_slug': self.chapter1.slug
                    }) + '?version=' + version_2,
            follow=False)
        self.assertEqual(result.status_code, 200)

        # and even to it using version 1 and old tuto slug !!
        result = self.client.get(
            reverse('content:view-container',
                    kwargs={
                        'pk': tuto.pk,
                        'slug': old_slug_tuto,
                        'container_slug': old_slug_part
                    }) + '?version=' + version_1,
            follow=False)
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse('content:view-container',
                    kwargs={
                        'pk': tuto.pk,
                        'slug': old_slug_tuto,
                        'parent_container_slug': old_slug_part,
                        'container_slug': self.chapter1.slug
                    }) + '?version=' + version_1,
            follow=False)
        self.assertEqual(result.status_code, 200)

        # but you can also access it with the current slug (for retro-compatibility)
        result = self.client.get(
            reverse('content:view-container',
                    kwargs={
                        'pk': tuto.pk,
                        'slug': tuto.slug,
                        'container_slug': old_slug_part
                    }) + '?version=' + version_1,
            follow=False)
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse('content:view-container',
                    kwargs={
                        'pk': tuto.pk,
                        'slug': tuto.slug,
                        'parent_container_slug': old_slug_part,
                        'container_slug': self.chapter1.slug
                    }) + '?version=' + version_1,
            follow=False)
        self.assertEqual(result.status_code, 200)

        # delete part
        result = self.client.post(
            reverse('content:delete',
                    kwargs={
                        'pk': tuto.pk,
                        'slug': tuto.slug,
                        'object_slug': current_slug_part
                    }),
            follow=False)
        self.assertEqual(result.status_code, 302)

        # we can still access to the part in version 3:
        result = self.client.get(
            reverse('content:view-container',
                    kwargs={
                        'pk': tuto.pk,
                        'slug': tuto.slug,
                        'container_slug': current_slug_part
                    }) + '?version=' + version_3,
            follow=False)
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse('content:view-container',
                    kwargs={
                        'pk': tuto.pk,
                        'slug': tuto.slug,
                        'parent_container_slug': current_slug_part,
                        'container_slug': self.chapter1.slug
                    }) + '?version=' + version_3,
            follow=False)

        # version 2:
        self.assertEqual(result.status_code, 200)
        result = self.client.get(
            reverse('content:view-container',
                    kwargs={
                        'pk': tuto.pk,
                        'slug': tuto.slug,
                        'container_slug': old_slug_part
                    }) + '?version=' + version_2,
            follow=False)
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse('content:view-container',
                    kwargs={
                        'pk': tuto.pk,
                        'slug': tuto.slug,
                        'parent_container_slug': old_slug_part,
                        'container_slug': self.chapter1.slug
                    }) + '?version=' + version_2,
            follow=False)
        self.assertEqual(result.status_code, 200)

        # version 1:
        result = self.client.get(
            reverse('content:view-container',
                    kwargs={
                        'pk': tuto.pk,
                        'slug': old_slug_tuto,
                        'container_slug': old_slug_part
                    }) + '?version=' + version_1,
            follow=False)
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse('content:view-container',
                    kwargs={
                        'pk': tuto.pk,
                        'slug': old_slug_tuto,
                        'parent_container_slug': old_slug_part,
                        'container_slug': self.chapter1.slug
                    }) + '?version=' + version_1,
            follow=False)
        self.assertEqual(result.status_code, 200)

    def test_if_none(self):
        """ensure that everything is ok if `None` is set"""

        # login with author
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)

        given_title = u'Un titre que personne ne lira'
        some_text = u'Tralalala !!'

        # let's cheat a little bit and use the "manual way" to force `None`
        tuto = PublishableContent.objects.get(pk=self.tuto.pk)
        versioned = tuto.load_version()
        sha = versioned.repo_add_container(given_title, None, None)
        new_container = versioned.children[-1]
        slug_new_container = versioned.children[-1].slug
        tuto.sha_draft = sha
        tuto.save()

        # test access
        result = self.client.get(
            reverse('content:view', args=[tuto.pk, tuto.slug]),
            follow=False)
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse('content:view-container',
                    kwargs={
                        'pk': tuto.pk,
                        'slug': tuto.slug,
                        'container_slug': slug_new_container
                    }),
            follow=False)
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse('content:edit-container',
                    kwargs={
                        'pk': tuto.pk,
                        'slug': tuto.slug,
                        'container_slug': slug_new_container,
                    }),
            follow=False)
        self.assertEqual(result.status_code, 200)  # access to edition page is ok

        # edit container:
        result = self.client.post(
            reverse('content:edit-container', kwargs={
                'pk': tuto.pk,
                'slug': tuto.slug,
                'container_slug': slug_new_container
            }),
            {
                'title': given_title,
                'introduction': some_text,
                'conclusion': some_text,
                'last_hash': new_container.compute_hash()
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        # test access
        result = self.client.get(
            reverse('content:view', args=[tuto.pk, tuto.slug]),
            follow=False)
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse('content:view-container',
                    kwargs={
                        'pk': tuto.pk,
                        'slug': tuto.slug,
                        'container_slug': slug_new_container
                    }),
            follow=False)
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse('content:edit-container',
                    kwargs={
                        'pk': tuto.pk,
                        'slug': tuto.slug,
                        'container_slug': slug_new_container
                    }),
            follow=False)
        self.assertEqual(result.status_code, 200)

    def test_export_content(self):
        """Test if content is exported well"""

        # login with author
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)

        given_title = u'Oh, le beau titre à lire !'
        some_text = u'À lire à un moment ou un autre, Über utile'  # accentuated characters are important for the test

        # create a tutorial
        result = self.client.post(
            reverse('content:create'),
            {
                'title': given_title,
                'description': some_text,
                'introduction': some_text,
                'conclusion': some_text,
                'type': u'TUTORIAL',
                'licence': self.licence.pk,
                'subcategory': self.subcategory.pk,
            },
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(PublishableContent.objects.all().count(), 2)

        tuto = PublishableContent.objects.last()
        tuto_pk = tuto.pk
        tuto_slug = tuto.slug

        # add a chapter
        result = self.client.post(
            reverse('content:create-container', args=[tuto_pk, tuto_slug]),
            {
                'title': given_title,
                'introduction': some_text,
                'conclusion': some_text
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        versioned = PublishableContent.objects.get(pk=tuto_pk).load_version()
        chapter = versioned.children[-1]

        # add extract to chapter
        result = self.client.post(
            reverse('content:create-extract',
                    kwargs={
                        'pk': tuto_pk,
                        'slug': tuto_slug,
                        'container_slug': chapter.slug
                    }),
            {
                'title': given_title,
                'text': some_text
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        # download
        result = self.client.get(
            reverse('content:download-zip', args=[tuto_pk, tuto_slug]),
            follow=False)
        self.assertEqual(result.status_code, 200)
        draft_zip_path = os.path.join(tempfile.gettempdir(), '__draft1.zip')
        f = open(draft_zip_path, 'w')
        f.write(result.content)
        f.close()

        versioned = PublishableContent.objects.get(pk=tuto_pk).load_version()
        version_1 = versioned.current_version
        chapter = versioned.children[-1]
        extract = chapter.children[-1]
        archive = zipfile.ZipFile(draft_zip_path, 'r')

        self.assertEqual(unicode(archive.read('manifest.json'), 'utf-8'), versioned.get_json())

        found = True
        try:  # to the person who try to modify this test: I'm sorry, but the test does not say where the error is ;)
            archive.getinfo('introduction.md')
            archive.getinfo('conclusion.md')
            archive.getinfo(os.path.join(chapter.slug, 'introduction.md'))
            archive.getinfo(os.path.join(chapter.slug, 'conclusion.md'))
            archive.getinfo(os.path.join(chapter.slug, 'conclusion.md'))
            archive.getinfo(extract.text)
        except KeyError:
            found = False

        self.assertTrue(found)

        where = ['introduction.md', 'conclusion.md', os.path.join(chapter.slug, 'introduction.md'),
                 os.path.join(chapter.slug, 'conclusion.md'), extract.text]

        for path in where:
            self.assertEqual(unicode(archive.read(path), 'utf-8'), some_text)

        # add another extract to chapter
        different_title = u'Un Über titre de la mort qui tue'  # one more times, mind accentuated characters !!
        different_text = u'þ is a letter as well ? ¶ means paragraph, at least'
        result = self.client.post(
            reverse('content:create-extract',
                    kwargs={
                        'pk': tuto_pk,
                        'slug': tuto_slug,
                        'container_slug': chapter.slug
                    }),
            {
                'title': different_title,
                'text': different_text
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        # download
        result = self.client.get(
            reverse('content:download-zip', args=[tuto_pk, tuto_slug]),
            follow=False)
        self.assertEqual(result.status_code, 200)
        draft_zip_path_2 = os.path.join(tempfile.gettempdir(), '__draft2.zip')
        f = open(draft_zip_path_2, 'w')
        f.write(result.content)
        f.close()

        versioned = PublishableContent.objects.get(pk=tuto_pk).load_version()
        version_2 = versioned.current_version
        extract2 = versioned.children[-1].children[-1]
        self.assertNotEqual(extract.slug, extract2.slug)  # just ensure that we don't pick the same extract
        self.assertNotEqual(version_1, version_2)  # just to ensure that something happen, somehow

        archive = zipfile.ZipFile(draft_zip_path_2, 'r')
        self.assertEqual(unicode(archive.read('manifest.json'), 'utf-8'), versioned.get_json())

        found = True
        try:
            archive.getinfo(extract2.text)
        except KeyError:
            found = False
        self.assertTrue(found)

        self.assertEqual(different_text, unicode(archive.read(extract2.text), 'utf-8'))

        # now, try versioned download:
        result = self.client.get(
            reverse('content:download-zip', args=[tuto_pk, tuto_slug]) + '?version=' + version_1,
            follow=False)
        self.assertEqual(result.status_code, 200)
        draft_zip_path_3 = os.path.join(tempfile.gettempdir(), '__draft3.zip')
        f = open(draft_zip_path_3, 'w')
        f.write(result.content)
        f.close()

        archive = zipfile.ZipFile(draft_zip_path_3, 'r')

        found = True
        try:
            archive.getinfo(extract2.text)
        except KeyError:
            found = False
        self.assertFalse(found)  # if we download the old version, the new extract introduced in version 2 is not in

        found = True
        try:
            archive.getinfo(extract.text)
        except KeyError:
            found = False
        self.assertTrue(found)  # but the extract of version 1 is in !

        # clean up our mess
        os.remove(draft_zip_path)
        os.remove(draft_zip_path_2)
        os.remove(draft_zip_path_3)

    def test_import_create_content(self):
        """Test if the importation of a tuto is working"""

        # login with author
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)

        given_title = u'Une autre histoire captivante'
        some_text = u'Il était une fois ... La suite.'

        # create a tutorial
        result = self.client.post(
            reverse('content:create'),
            {
                'title': given_title,
                'description': some_text,
                'introduction': some_text,
                'conclusion': some_text,
                'type': u'TUTORIAL',
                'licence': self.licence.pk,
                'subcategory': self.subcategory.pk,
            },
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(PublishableContent.objects.all().count(), 2)

        tuto = PublishableContent.objects.last()
        tuto_pk = tuto.pk
        tuto_slug = tuto.slug

        # add a chapter
        result = self.client.post(
            reverse('content:create-container', args=[tuto_pk, tuto_slug]),
            {
                'title': given_title,
                'introduction': some_text,
                'conclusion': some_text
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        versioned = PublishableContent.objects.get(pk=tuto_pk).load_version()
        chapter = versioned.children[-1]

        # add extract to chapter
        result = self.client.post(
            reverse('content:create-extract',
                    kwargs={
                        'pk': tuto_pk,
                        'slug': tuto_slug,
                        'container_slug': chapter.slug
                    }),
            {
                'title': given_title,
                'text': some_text
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        # download
        result = self.client.get(
            reverse('content:download-zip', args=[tuto_pk, tuto_slug]),
            follow=False)
        self.assertEqual(result.status_code, 200)
        draft_zip_path = os.path.join(tempfile.gettempdir(), '__draft1.zip')
        f = open(draft_zip_path, 'w')
        f.write(result.content)
        f.close()

        first_version = PublishableContent.objects.get(pk=tuto_pk).load_version()

        # then, use the archive to create a new content (which will be a copy of this one)
        result = self.client.post(
            reverse('content:import-new'),
            {
                'archive': open(draft_zip_path),
                'subcategory': self.subcategory.pk
            },
            follow=False
        )
        self.assertEqual(result.status_code, 302)

        self.assertEqual(PublishableContent.objects.count(), 3)
        new_tuto = PublishableContent.objects.last()
        self.assertNotEqual(new_tuto.pk, tuto_pk)  # those are two different content !

        # first, test if values are correctly set in DB
        self.assertEqual(new_tuto.title, tuto.title)
        self.assertEqual(new_tuto.description, tuto.description)
        self.assertEqual(new_tuto.licence, tuto.licence)
        self.assertEqual(new_tuto.type, tuto.type)

        self.assertNotEqual(new_tuto.slug, tuto_slug)  # slug should NEVER be the same !!

        # then, let's do the same for the versioned one
        versioned = new_tuto.load_version()

        self.assertEqual(first_version.title, versioned.title)
        self.assertEqual(first_version.description, versioned.description)
        self.assertEqual(first_version.licence, versioned.licence)
        self.assertEqual(first_version.type, versioned.type)

        # ensure the content
        self.assertEqual(versioned.get_introduction(), some_text)
        self.assertEqual(versioned.get_introduction(), some_text)
        self.assertEqual(len(versioned.children), 1)

        new_chapter = versioned.children[-1]
        self.assertEqual(new_chapter.get_introduction(), some_text)
        self.assertEqual(new_chapter.get_conclusion(), some_text)
        self.assertEqual(len(new_chapter.children), 1)

        extract = new_chapter.children[-1]
        self.assertEqual(extract.get_text(), some_text)

    def test_import_in_existing_content(self):
        """Test if the importation of a content into another is working"""

        # login with author
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)

        given_title = u'Parce que le texte change à chaque fois'
        some_text = u'Sinon, c\'pas drôle'

        # create a tutorial
        result = self.client.post(
            reverse('content:create'),
            {
                'title': given_title,
                'description': some_text,
                'introduction': some_text,
                'conclusion': some_text,
                'type': u'TUTORIAL',
                'licence': self.licence.pk,
                'subcategory': self.subcategory.pk,
            },
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(PublishableContent.objects.all().count(), 2)

        tuto = PublishableContent.objects.last()
        tuto_pk = tuto.pk
        tuto_slug = tuto.slug

        # add a chapter
        result = self.client.post(
            reverse('content:create-container', args=[tuto_pk, tuto_slug]),
            {
                'title': given_title,
                'introduction': some_text,
                'conclusion': some_text
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        versioned = PublishableContent.objects.get(pk=tuto_pk).load_version()
        chapter = versioned.children[-1]

        # add extract to chapter
        result = self.client.post(
            reverse('content:create-extract',
                    kwargs={
                        'pk': tuto_pk,
                        'slug': tuto_slug,
                        'container_slug': chapter.slug
                    }),
            {
                'title': given_title,
                'text': some_text
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        # download
        result = self.client.get(
            reverse('content:download-zip', args=[tuto_pk, tuto_slug]),
            follow=False)
        self.assertEqual(result.status_code, 200)
        draft_zip_path = os.path.join(tempfile.gettempdir(), '__draft1.zip')
        f = open(draft_zip_path, 'w')
        f.write(result.content)
        f.close()

        first_version = PublishableContent.objects.get(pk=tuto_pk).load_version()

        # then, use the archive to create a new content (which will be a copy of this one)
        result = self.client.post(
            reverse('content:import', kwargs={'pk': self.tuto.pk, 'slug': self.tuto.slug}),
            {
                'archive': open(draft_zip_path),
                'subcategory': self.subcategory.pk
            },
            follow=False
        )
        self.assertEqual(result.status_code, 302)

        self.assertEqual(PublishableContent.objects.count(), 2)
        existing_tuto = PublishableContent.objects.get(pk=self.tuto.pk)
        self.assertNotEqual(existing_tuto.pk, tuto_pk)  # those are two different content !

        # first, test if values are correctly set in DB
        self.assertEqual(existing_tuto.title, tuto.title)
        self.assertEqual(existing_tuto.description, tuto.description)
        self.assertEqual(existing_tuto.licence, tuto.licence)
        self.assertEqual(existing_tuto.type, tuto.type)

        self.assertNotEqual(existing_tuto.slug, tuto_slug)  # slug should NEVER be the same !!

        # then, let's do the same for the versioned one
        versioned = existing_tuto.load_version()

        self.assertEqual(first_version.title, versioned.title)
        self.assertEqual(first_version.description, versioned.description)
        self.assertEqual(first_version.licence, versioned.licence)
        self.assertEqual(first_version.type, versioned.type)

        # ensure the content
        self.assertEqual(versioned.get_introduction(), some_text)
        self.assertEqual(versioned.get_introduction(), some_text)
        self.assertEqual(len(versioned.children), 1)

        new_chapter = versioned.children[-1]
        self.assertEqual(new_chapter.get_introduction(), some_text)
        self.assertEqual(new_chapter.get_conclusion(), some_text)
        self.assertEqual(len(new_chapter.children), 1)

        extract = new_chapter.children[-1]
        self.assertEqual(extract.get_text(), some_text)

    def test_diff_for_new_content(self):
        # login with author
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)

        # create tutorial
        intro = u'une intro'
        conclusion = u'une conclusion'
        description = u'une description'
        title = u'un titre'
        result = self.client.post(
            reverse('content:create'),
            {
                'title': title,
                'description': description,
                'introduction': intro,
                'conclusion': conclusion,
                'type': u'TUTORIAL',
                'licence': self.licence.pk,
                'subcategory': self.subcategory.pk,
            },
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(PublishableContent.objects.all().count(), 2)
        new_content = PublishableContent.objects.last()
        result = self.client.get(
            reverse('content:diff', kwargs={
                'pk': new_content.pk,
                'slug': new_content.slug
            })
        )
        self.assertEqual(200, result.status_code)

    def test_validation_workflow(self):
        """test the different case of validation"""

        text_validation = u'Valide moi ce truc, s\'il te plait'
        source = u'http://example.com'  # thanks the IANA on that one ;-)
        different_source = u'http://example.org'
        text_accept = u'C\'est de la m***, mais ok, j\'accepte'
        text_reject = u'Je refuse ce truc, arbitrairement !'

        # let's create a medium-size tutorial
        midsize_tuto = PublishableContentFactory(type='TUTORIAL')

        midsize_tuto.authors.add(self.user_author)
        midsize_tuto.gallery = GalleryFactory()
        midsize_tuto.licence = self.licence
        midsize_tuto.save()

        # populate with 2 chapters (1 extract each)
        midsize_tuto_draft = midsize_tuto.load_version()
        chapter1 = ContainerFactory(parent=midsize_tuto_draft, db_objet=midsize_tuto)
        ExtractFactory(container=chapter1, db_object=midsize_tuto)
        chapter2 = ContainerFactory(parent=midsize_tuto_draft, db_objet=midsize_tuto)
        ExtractFactory(container=chapter2, db_object=midsize_tuto)

        # connect with author:
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)

        # ask validation
        self.assertEqual(Validation.objects.count(), 0)

        result = self.client.post(
            reverse('validation:ask', kwargs={'pk': midsize_tuto.pk, 'slug': midsize_tuto.slug}),
            {
                'text': '',
                'source': source,
                'version': midsize_tuto_draft.current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Validation.objects.count(), 0)  # not working if you don't provide a text

        result = self.client.post(
            reverse('validation:ask', kwargs={'pk': midsize_tuto.pk, 'slug': midsize_tuto.slug}),
            {
                'text': text_validation,
                'source': source,
                'version': midsize_tuto_draft.current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Validation.objects.count(), 1)

        self.assertEqual(PublishableContent.objects.get(pk=midsize_tuto.pk).source, source)  # source is set

        validation = Validation.objects.filter(content=midsize_tuto).last()
        self.assertIsNotNone(validation)

        self.assertEqual(validation.comment_authors, text_validation)
        self.assertEqual(validation.version, midsize_tuto_draft.current_version)
        self.assertEqual(validation.status, 'PENDING')

        # ensure that author cannot publish himself
        result = self.client.post(
            reverse('validation:reserve', kwargs={'pk': validation.pk}),
            {
                'version': validation.version
            },
            follow=False)
        self.assertEqual(result.status_code, 403)

        result = self.client.post(
            reverse('validation:accept', kwargs={'pk': validation.pk}),
            {
                'text': text_accept,
                'is_major': True,
                'source': u''
            },
            follow=False)
        self.assertEqual(result.status_code, 403)

        self.assertEqual(Validation.objects.filter(content=midsize_tuto).last().status, 'PENDING')

        # logout, then login with guest
        self.client.logout()

        result = self.client.get(
            reverse('content:view', kwargs={'pk': midsize_tuto.pk, 'slug': midsize_tuto.slug}) +
            '?version=' + validation.version,
            follow=False)
        self.assertEqual(result.status_code, 302)  # no, public cannot access a tutorial in validation ...

        self.assertEqual(
            self.client.login(
                username=self.user_guest.username,
                password='hostel77'),
            True)

        result = self.client.get(
            reverse('content:view', kwargs={'pk': midsize_tuto.pk, 'slug': midsize_tuto.slug}) +
            '?version=' + validation.version,
            follow=False)
        self.assertEqual(result.status_code, 403)  # ... Same for guest ...

        # then try with staff
        self.client.logout()
        self.assertEqual(
            self.client.login(
                username=self.user_staff.username,
                password='hostel77'),
            True)

        result = self.client.get(
            reverse('content:view', kwargs={'pk': midsize_tuto.pk, 'slug': midsize_tuto.slug}) +
            '?version=' + validation.version,
            follow=False)
        self.assertEqual(result.status_code, 200)  # ... But staff can, obviously !

        # reserve tuto:
        result = self.client.post(
            reverse('validation:reserve', kwargs={'pk': validation.pk}),
            {
                'version': validation.version
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        validation = Validation.objects.filter(pk=validation.pk).last()
        self.assertEqual(validation.status, 'PENDING_V')
        self.assertEqual(validation.validator, self.user_staff)

        # unreserve
        result = self.client.post(
            reverse('validation:reserve', kwargs={'pk': validation.pk}),
            {
                'version': validation.version
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        validation = Validation.objects.filter(pk=validation.pk).last()
        self.assertEqual(validation.status, 'PENDING')
        self.assertEqual(validation.validator, None)

        # re-reserve
        result = self.client.post(
            reverse('validation:reserve', kwargs={'pk': validation.pk}),
            {
                'version': validation.version
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        validation = Validation.objects.filter(pk=validation.pk).last()
        self.assertEqual(validation.status, 'PENDING_V')
        self.assertEqual(validation.validator, self.user_staff)

        # let's modify the tutorial and ask for a new validation :
        ExtractFactory(container=chapter2, db_object=midsize_tuto)
        midsize_tuto = PublishableContent.objects.get(pk=midsize_tuto.pk)
        midsize_tuto_draft = midsize_tuto.load_version()

        result = self.client.post(
            reverse('validation:ask', kwargs={'pk': midsize_tuto.pk, 'slug': midsize_tuto.slug}),
            {
                'text': text_validation,
                'source': source,
                'version': midsize_tuto_draft.current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Validation.objects.count(), 2)

        self.assertEqual(Validation.objects.get(pk=validation.pk).status, 'CANCEL')  # previous is canceled

        # ... Therefore, a new Validation object is created
        validation = Validation.objects.filter(content=midsize_tuto).last()
        self.assertEqual(validation.status, 'PENDING')
        self.assertEqual(validation.validator, None)
        self.assertEqual(validation.version, midsize_tuto_draft.current_version)

        self.assertEqual(PublishableContent.objects.get(pk=midsize_tuto.pk).sha_validation,
                         midsize_tuto_draft.current_version)

        self.assertEqual(PrivateTopic.objects.last().author, self.user_staff)  # admin has received a PM

        # re-re-reserve (!)
        result = self.client.post(
            reverse('validation:reserve', kwargs={'pk': validation.pk}),
            {
                'version': validation.version
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        validation = Validation.objects.filter(pk=validation.pk).last()
        self.assertEqual(validation.status, 'PENDING_V')
        self.assertEqual(validation.validator, self.user_staff)

        # ensure that author cannot publish himself
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)

        result = self.client.post(
            reverse('validation:accept', kwargs={'pk': validation.pk}),
            {
                'text': text_accept,
                'is_major': True,
                'source': u''
            },
            follow=False)
        self.assertEqual(result.status_code, 403)

        self.assertEqual(Validation.objects.filter(content=midsize_tuto).last().status, 'PENDING_V')

        # reject it with staff !
        self.assertEqual(
            self.client.login(
                username=self.user_staff.username,
                password='hostel77'),
            True)

        result = self.client.post(
            reverse('validation:reject', kwargs={'pk': validation.pk}),
            {
                'text': ''
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        validation = Validation.objects.filter(pk=validation.pk).last()
        self.assertEqual(validation.status, 'PENDING_V')  # rejection is impossible without text

        result = self.client.post(
            reverse('validation:reject', kwargs={'pk': validation.pk}),
            {
                'text': text_reject
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        validation = Validation.objects.filter(pk=validation.pk).last()
        self.assertEqual(validation.status, 'REJECT')
        self.assertEqual(validation.comment_validator, text_reject)

        self.assertIsNone(PublishableContent.objects.get(pk=midsize_tuto.pk).sha_validation)

        self.assertEqual(PrivateTopic.objects.last().author, self.user_author)  # author has received a PM

        # re-ask for validation
        result = self.client.post(
            reverse('validation:ask', kwargs={'pk': midsize_tuto.pk, 'slug': midsize_tuto.slug}),
            {
                'text': text_validation,
                'source': source,
                'version': midsize_tuto_draft.current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Validation.objects.filter(content=midsize_tuto).count(), 3)

        # a new object is created !
        validation = Validation.objects.filter(content=midsize_tuto).last()
        self.assertEqual(validation.status, 'PENDING')
        self.assertEqual(validation.validator, None)
        self.assertEqual(validation.version, midsize_tuto_draft.current_version)

        result = self.client.post(
            reverse('validation:reserve', kwargs={'pk': validation.pk}),
            {
                'version': validation.version
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        validation = Validation.objects.filter(pk=validation.pk).last()
        self.assertEqual(validation.status, 'PENDING_V')
        self.assertEqual(validation.validator, self.user_staff)
        self.assertEqual(validation.version, midsize_tuto_draft.current_version)

        # accept
        result = self.client.post(
            reverse('validation:accept', kwargs={'pk': validation.pk}),
            {
                'text': '',
                'is_major': True,
                'source': ''
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        validation = Validation.objects.filter(pk=validation.pk).last()
        self.assertEqual(validation.status, 'PENDING_V')  # acceptation is not possible without text

        result = self.client.post(
            reverse('validation:accept', kwargs={'pk': validation.pk}),
            {
                'text': text_accept,
                'is_major': True,
                'source': different_source  # because ;)
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        self.assertEqual(Validation.objects.filter(content=midsize_tuto).count(), 3)

        validation = Validation.objects.filter(pk=validation.pk).last()
        self.assertEqual(validation.status, 'ACCEPT')
        self.assertEqual(validation.comment_validator, text_accept)

        self.assertIsNone(PublishableContent.objects.get(pk=midsize_tuto.pk).sha_validation)

        self.assertEqual(PrivateTopic.objects.filter(author=self.user_author).count(), 2)
        self.assertEqual(PrivateTopic.objects.last().author, self.user_author)  # author has received another PM

        self.assertEqual(PublishedContent.objects.filter(content=midsize_tuto).count(), 1)
        published = PublishedContent.objects.filter(content=midsize_tuto).first()

        self.assertEqual(published.content.source, different_source)
        self.assertEqual(published.content_public_slug, midsize_tuto_draft.slug)
        self.assertTrue(os.path.exists(published.get_prod_path()))
        # ... another test cover the file creation and so all, lets skip this part

        # ensure that author cannot revoke his own publication
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)

        result = self.client.post(
            reverse('validation:revoke', kwargs={'pk': midsize_tuto.pk, 'slug': midsize_tuto.slug}),
            {
                'text': text_reject,
                'version': published.sha_public
            },
            follow=False)
        self.assertEqual(result.status_code, 403)
        self.assertEqual(Validation.objects.filter(content=midsize_tuto).last().status, 'ACCEPT')

        # revoke publication with staff
        self.assertEqual(
            self.client.login(
                username=self.user_staff.username,
                password='hostel77'),
            True)

        result = self.client.post(
            reverse('validation:revoke', kwargs={'pk': midsize_tuto.pk, 'slug': midsize_tuto.slug}),
            {
                'text': '',
                'version': published.sha_public
            },
            follow=False)

        validation = Validation.objects.filter(content=midsize_tuto).last()
        self.assertEqual(validation.status, 'ACCEPT')  # with no text, revocation is not possible

        result = self.client.post(
            reverse('validation:revoke', kwargs={'pk': midsize_tuto.pk, 'slug': midsize_tuto.slug}),
            {
                'text': text_reject,
                'version': published.sha_public
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        self.assertEqual(Validation.objects.filter(content=midsize_tuto).count(), 3)

        validation = Validation.objects.filter(content=midsize_tuto).last()
        self.assertEqual(validation.status, 'PENDING')
        self.assertEqual(validation.version, midsize_tuto.sha_draft)

        self.assertIsNotNone(PublishableContent.objects.get(pk=midsize_tuto.pk).sha_validation)

        self.assertEqual(PublishedContent.objects.filter(content=midsize_tuto).count(), 0)
        self.assertFalse(os.path.exists(published.get_prod_path()))

        self.assertEqual(PrivateTopic.objects.filter(author=self.user_author).count(), 3)
        self.assertEqual(PrivateTopic.objects.last().author, self.user_author)  # author has received another PM

        # so, reserve it
        result = self.client.post(
            reverse('validation:reserve', kwargs={'pk': validation.pk}),
            {
                'version': validation.version
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        validation = Validation.objects.filter(content=midsize_tuto).last()
        self.assertEqual(validation.status, 'PENDING_V')
        self.assertEqual(validation.validator, self.user_staff)

        # ... and cancel reservation with author
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)

        result = self.client.post(
            reverse('validation:cancel', kwargs={'pk': validation.pk}), follow=False)
        self.assertEqual(result.status_code, 302)

        self.assertEqual(Validation.objects.filter(content=midsize_tuto).count(), 3)

        validation = Validation.objects.filter(content=midsize_tuto).last()
        self.assertEqual(validation.status, 'CANCEL')  # the validation got canceled

        self.assertEqual(PrivateTopic.objects.filter(author=self.user_staff).count(), 2)
        self.assertEqual(PrivateTopic.objects.last().author, self.user_staff)  # admin has received another PM

    def test_public_access(self):
        """Test that everybody have access to a content after its publication"""

        text_validation = u'Valide moi ce truc, please !'
        text_publication = u'Aussi tôt dit, aussi tôt fait !'

        # 1. Article:
        article = PublishableContentFactory(type='ARTICLE')

        article.authors.add(self.user_author)
        article.gallery = GalleryFactory()
        article.licence = self.licence
        article.save()

        # populate the article
        article_draft = article.load_version()
        ExtractFactory(container=article_draft, db_object=article)
        ExtractFactory(container=article_draft, db_object=article)

        # connect with author:
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)

        # ask validation
        self.assertEqual(Validation.objects.count(), 0)

        result = self.client.post(
            reverse('validation:ask', kwargs={'pk': article.pk, 'slug': article.slug}),
            {
                'text': text_validation,
                'source': '',
                'version': article_draft.current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        # login with staff and publish
        self.assertEqual(
            self.client.login(
                username=self.user_staff.username,
                password='hostel77'),
            True)

        validation = Validation.objects.filter(content=article).last()

        result = self.client.post(
            reverse('validation:reserve', kwargs={'pk': validation.pk}),
            {
                'version': validation.version
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        # accept
        result = self.client.post(
            reverse('validation:accept', kwargs={'pk': validation.pk}),
            {
                'text': text_publication,
                'is_major': True,
                'source': u''
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        published = PublishedContent.objects.filter(content=article).first()
        self.assertIsNotNone(published)

        # test access to staff
        result = self.client.get(reverse('article:view', kwargs={'pk': article.pk, 'slug': article_draft.slug}))
        self.assertEqual(result.status_code, 200)

        # test access to public
        self.client.logout()
        result = self.client.get(reverse('article:view', kwargs={'pk': article.pk, 'slug': article_draft.slug}))
        self.assertEqual(result.status_code, 200)

        # test access for guest user
        self.assertEqual(
            self.client.login(
                username=self.user_guest.username,
                password='hostel77'),
            True)
        result = self.client.get(reverse('article:view', kwargs={'pk': article.pk, 'slug': article_draft.slug}))
        self.assertEqual(result.status_code, 200)

        # 2. middle-size tutorial (just to test the access to chapters)
        midsize_tuto = PublishableContentFactory(type='TUTORIAL')

        midsize_tuto.authors.add(self.user_author)
        midsize_tuto.gallery = GalleryFactory()
        midsize_tuto.licence = self.licence
        midsize_tuto.save()

        # populate the midsize_tuto
        midsize_tuto_draft = midsize_tuto.load_version()
        chapter1 = ContainerFactory(parent=midsize_tuto_draft, db_object=midsize_tuto)
        ExtractFactory(container=chapter1, db_object=midsize_tuto)

        # connect with author:
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)

        # ask validation
        result = self.client.post(
            reverse('validation:ask', kwargs={'pk': midsize_tuto.pk, 'slug': midsize_tuto.slug}),
            {
                'text': text_validation,
                'source': '',
                'version': midsize_tuto_draft.current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        # login with staff and publish
        self.assertEqual(
            self.client.login(
                username=self.user_staff.username,
                password='hostel77'),
            True)

        validation = Validation.objects.filter(content=midsize_tuto).last()

        result = self.client.post(
            reverse('validation:reserve', kwargs={'pk': validation.pk}),
            {
                'version': validation.version
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        # accept
        result = self.client.post(
            reverse('validation:accept', kwargs={'pk': validation.pk}),
            {
                'text': text_publication,
                'is_major': True,
                'source': u''
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        published = PublishedContent.objects.filter(content=midsize_tuto).first()
        self.assertIsNotNone(published)

        # test access to staff
        result = self.client.get(
            reverse('tutorial:view', kwargs={'pk': midsize_tuto.pk, 'slug': midsize_tuto_draft.slug}))
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse('tutorial:view-container',
                    kwargs={
                        'pk': midsize_tuto.pk,
                        'slug': midsize_tuto_draft.slug,
                        'container_slug': chapter1.slug
                    }))
        self.assertEqual(result.status_code, 200)

        # test access to public
        self.client.logout()
        result = self.client.get(
            reverse('tutorial:view', kwargs={'pk': midsize_tuto.pk, 'slug': midsize_tuto_draft.slug}))
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse('tutorial:view-container',
                    kwargs={
                        'pk': midsize_tuto.pk,
                        'slug': midsize_tuto_draft.slug,
                        'container_slug': chapter1.slug
                    }))
        self.assertEqual(result.status_code, 200)

        # test access for guest user
        self.assertEqual(
            self.client.login(
                username=self.user_guest.username,
                password='hostel77'),
            True)
        result = self.client.get(
            reverse('tutorial:view', kwargs={'pk': midsize_tuto.pk, 'slug': midsize_tuto_draft.slug}))
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse('tutorial:view-container',
                    kwargs={
                        'pk': midsize_tuto.pk,
                        'slug': midsize_tuto_draft.slug,
                        'container_slug': chapter1.slug
                    }))
        self.assertEqual(result.status_code, 200)

        # 3. a big tutorial (just to test the access to parts and chapters)
        bigtuto = PublishableContentFactory(type='TUTORIAL')

        bigtuto.authors.add(self.user_author)
        bigtuto.gallery = GalleryFactory()
        bigtuto.licence = self.licence
        bigtuto.save()

        # populate the bigtuto
        bigtuto_draft = bigtuto.load_version()
        part1 = ContainerFactory(parent=bigtuto_draft, db_object=bigtuto)
        chapter1 = ContainerFactory(parent=part1, db_object=bigtuto)
        ExtractFactory(container=chapter1, db_object=bigtuto)

        # connect with author:
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)

        # ask validation
        result = self.client.post(
            reverse('validation:ask', kwargs={'pk': bigtuto.pk, 'slug': bigtuto.slug}),
            {
                'text': text_validation,
                'source': '',
                'version': bigtuto_draft.current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        # login with staff and publish
        self.assertEqual(
            self.client.login(
                username=self.user_staff.username,
                password='hostel77'),
            True)

        validation = Validation.objects.filter(content=bigtuto).last()

        result = self.client.post(
            reverse('validation:reserve', kwargs={'pk': validation.pk}),
            {
                'version': validation.version
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        # accept
        result = self.client.post(
            reverse('validation:accept', kwargs={'pk': validation.pk}),
            {
                'text': text_publication,
                'is_major': True,
                'source': u''
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        published = PublishedContent.objects.filter(content=bigtuto).first()
        self.assertIsNotNone(published)

        # test access to staff
        result = self.client.get(
            reverse('tutorial:view', kwargs={'pk': bigtuto.pk, 'slug': bigtuto_draft.slug}))
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse('tutorial:view-container',
                    kwargs={
                        'pk': bigtuto.pk,
                        'slug': bigtuto_draft.slug,
                        'container_slug': part1.slug
                    }))
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse('tutorial:view-container',
                    kwargs={
                        'pk': bigtuto.pk,
                        'slug': bigtuto_draft.slug,
                        'parent_container_slug': part1.slug,
                        'container_slug': chapter1.slug
                    }))
        self.assertEqual(result.status_code, 200)

        # test access to public
        self.client.logout()
        result = self.client.get(
            reverse('tutorial:view', kwargs={'pk': bigtuto.pk, 'slug': bigtuto_draft.slug}))
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse('tutorial:view-container',
                    kwargs={
                        'pk': bigtuto.pk,
                        'slug': bigtuto_draft.slug,
                        'container_slug': part1.slug
                    }))
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse('tutorial:view-container',
                    kwargs={
                        'pk': bigtuto.pk,
                        'slug': bigtuto_draft.slug,
                        'parent_container_slug': part1.slug,
                        'container_slug': chapter1.slug
                    }))
        self.assertEqual(result.status_code, 200)

        # test access for guest user
        self.assertEqual(
            self.client.login(
                username=self.user_guest.username,
                password='hostel77'),
            True)
        result = self.client.get(
            reverse('tutorial:view', kwargs={'pk': bigtuto.pk, 'slug': bigtuto_draft.slug}))
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse('tutorial:view-container',
                    kwargs={
                        'pk': bigtuto.pk,
                        'slug': bigtuto_draft.slug,
                        'container_slug': part1.slug
                    }))
        self.assertEqual(result.status_code, 200)

        result = self.client.get(
            reverse('tutorial:view-container',
                    kwargs={
                        'pk': bigtuto.pk,
                        'slug': bigtuto_draft.slug,
                        'parent_container_slug': part1.slug,
                        'container_slug': chapter1.slug
                    }))
        self.assertEqual(result.status_code, 200)

        # just for the fun of it, lets then revoke publication
        self.assertEqual(
            self.client.login(
                username=self.user_staff.username,
                password='hostel77'),
            True)

        result = self.client.post(
            reverse('validation:revoke', kwargs={'pk': bigtuto.pk, 'slug': bigtuto.slug}),
            {
                'text': u'Pour le fun',
                'version': bigtuto_draft.current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        # now, let's get a whole bunch of good old fashioned 404 (and not 403 or 302 !!)
        result = self.client.get(
            reverse('tutorial:view', kwargs={'pk': bigtuto.pk, 'slug': bigtuto_draft.slug}))
        self.assertEqual(result.status_code, 404)

        result = self.client.get(
            reverse('tutorial:view-container',
                    kwargs={
                        'pk': bigtuto.pk,
                        'slug': bigtuto_draft.slug,
                        'container_slug': part1.slug
                    }))
        self.assertEqual(result.status_code, 404)

        result = self.client.get(
            reverse('tutorial:view-container',
                    kwargs={
                        'pk': bigtuto.pk,
                        'slug': bigtuto_draft.slug,
                        'parent_container_slug': part1.slug,
                        'container_slug': chapter1.slug
                    }))
        self.assertEqual(result.status_code, 404)

        # test access to public
        self.client.logout()
        result = self.client.get(
            reverse('tutorial:view', kwargs={'pk': bigtuto.pk, 'slug': bigtuto_draft.slug}))
        self.assertEqual(result.status_code, 404)

        result = self.client.get(
            reverse('tutorial:view-container',
                    kwargs={
                        'pk': bigtuto.pk,
                        'slug': bigtuto_draft.slug,
                        'container_slug': part1.slug
                    }))
        self.assertEqual(result.status_code, 404)

        result = self.client.get(
            reverse('tutorial:view-container',
                    kwargs={
                        'pk': bigtuto.pk,
                        'slug': bigtuto_draft.slug,
                        'parent_container_slug': part1.slug,
                        'container_slug': chapter1.slug
                    }))
        self.assertEqual(result.status_code, 404)

        # test access for guest user
        self.assertEqual(
            self.client.login(
                username=self.user_guest.username,
                password='hostel77'),
            True)

        result = self.client.get(
            reverse('tutorial:view', kwargs={'pk': bigtuto.pk, 'slug': bigtuto_draft.slug}))
        self.assertEqual(result.status_code, 404)

        result = self.client.get(
            reverse('tutorial:view-container',
                    kwargs={
                        'pk': bigtuto.pk,
                        'slug': bigtuto_draft.slug,
                        'container_slug': part1.slug
                    }))
        self.assertEqual(result.status_code, 404)

        result = self.client.get(
            reverse('tutorial:view-container',
                    kwargs={
                        'pk': bigtuto.pk,
                        'slug': bigtuto_draft.slug,
                        'parent_container_slug': part1.slug,
                        'container_slug': chapter1.slug
                    }))
        self.assertEqual(result.status_code, 404)

    def test_js_fiddle_activation(self):

        login_check = self.client.login(
            username=self.staff.username,
            password='hostel77')
        self.assertEqual(login_check, True)
        result = self.client.post(
            reverse('content:activate-jsfiddle'),
            {
                "pk": self.tuto.pk,
                "js_support": "on"
            }, follow=True)
        self.assertEqual(result.status_code, 200)
        updated = PublishableContent.objects.get(pk=self.tuto.pk)
        self.assertTrue(updated.js_support)
        result = self.client.post(
            reverse('content:activate-jsfiddle'),
            {
                "pk": self.tuto.pk,
            }, follow=True)
        self.assertEqual(result.status_code, 200)
        updated = PublishableContent.objects.get(pk=self.tuto.pk)
        self.assertFalse(updated.js_support)
        self.client.logout()
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)
        result = self.client.post(
            reverse('content:activate-jsfiddle'),
            {
                "pk": self.tuto.pk,
                "js_support": True
            })
        self.assertEqual(result.status_code, 403)

    def test_add_note(self):
        tuto = PublishedContentFactory(author_list=[self.user_author], type="TUTORIAL")

        published_obj = PublishedContent.objects \
            .filter(content_pk=tuto.pk, content_public_slug=tuto.slug, content_type=tuto.type) \
            .prefetch_related('content') \
            .prefetch_related("content__authors") \
            .prefetch_related("content__subcategory") \
            .first()

        self.assertIsNotNone(published_obj)

        self.assertEqual(
            self.client.login(
                username=self.user_guest.username,
                password='hostel77'),
            True)

        result = self.client.post(
            reverse("content:add-reaction") + u'?pk={}'.format(published_obj.content.pk),
            {
                'text': u'message',
                'last_note': '0'
            }, follow=True)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(ContentReaction.objects.count(), 1)
        self.assertEqual(self.client.get(reverse("tutorial:view", args=[tuto.pk, tuto.slug])).status_code, 200)
        result = self.client.post(
            reverse("content:add-reaction") + u'?clementine={}'.format(published_obj.content.pk),
            {
                'text': u'message',
                'last_note': '0'
            }, follow=True)
        self.assertEqual(result.status_code, 404)

    def test_validate_unexisting(self):

        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)
        result = self.client.post(
            reverse('validation:ask', kwargs={'pk': self.tuto.pk, 'slug': self.tuto.slug}),
            {
                'text': "blaaaaa",
                'source': "",
                'version': "unexistingversion"
            },
            follow=False)
        self.assertEqual(Validation.objects.filter(content__pk=self.tuto.pk).count(), 0)
        self.assertEqual(result.status_code, 404)

    def test_help_to_perfect_tuto(self):
        """ This test aim to unit test the "help me to write my tutorial" interface.
        It is testing if the back-end is always sending back good datas"""

        # create some helps:
        num_of_helps = 5  # note: should be at least "2" for this test to be performed
        for i in range(num_of_helps):
            a = HelpWritingFactory()
            a.save()

        helps = HelpWriting.objects.all()

        # currently the tutorial is published with no beta, so back-end should return 0 tutorial
        response = self.client.get(
            reverse('content:helps'),
            follow=False
        )

        self.assertEqual(200, response.status_code)
        contents = response.context['contents']
        self.assertEqual(len(contents), 0)

        # then active the beta on tutorial :
        # first, login with author :
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)

        sha_draft = PublishableContent.objects.get(pk=self.tuto.pk).sha_draft
        response = self.client.post(
            reverse('content:set-beta', kwargs={'pk': self.tuto.pk, 'slug': self.tuto.slug}),
            {
                'version': sha_draft
            },
            follow=False
        )
        self.assertEqual(302, response.status_code)
        sha_beta = PublishableContent.objects.get(pk=self.tuto.pk).sha_beta
        self.assertEqual(sha_draft, sha_beta)

        response = self.client.get(
            reverse('content:helps'),
            follow=False
        )
        self.assertEqual(200, response.status_code)
        contents = response.context['contents']
        self.assertEqual(len(contents), 1)

        # However if we ask with a filter we will still get 0 !
        for helping in helps:
            response = self.client.get(
                reverse('content:helps') +
                u'?need={}'.format(helping.slug),
                follow=False
            )
            self.assertEqual(200, response.status_code)
            contents = response.context['contents']
            self.assertEqual(len(contents), 0)

        # now tutorial is positive for every options
        # if we ask for any help we should get a positive answer for every filter !
        self.tuto = PublishableContent.objects.get(pk=self.tuto.pk)
        for helping in helps:
            self.tuto.helps.add(helping)
        self.tuto.save()

        for helping in helps:
            response = self.client.get(
                reverse('content:helps') +
                u'?need={}'.format(helping.slug),
                follow=False
            )
            self.assertEqual(200, response.status_code)
            contents = response.context['contents']
            self.assertEqual(len(contents), 1)

        # now, add an article
        article = PublishableContentFactory(type="ARTICLE")
        article.authors.add(self.user_author)
        article.subcategory.add(self.subcategory)
        article.save()

        # in the helps, there should still be only one results
        response = self.client.get(
            reverse('content:helps'),
            follow=False
        )
        self.assertEqual(200, response.status_code)
        contents = response.context['contents']
        self.assertEqual(len(contents), 1)

        # test "type" filter
        response = self.client.get(
            reverse('content:helps') +
            u'?type=article',
            follow=False
        )
        self.assertEqual(200, response.status_code)
        contents = response.context['contents']
        self.assertEqual(len(contents), 0)  # no article yet

        response = self.client.get(
            reverse('content:helps') +
            u'?type=tuto',
            follow=False
        )
        self.assertEqual(200, response.status_code)
        contents = response.context['contents']
        self.assertEqual(len(contents), 1)

        # add an help
        an_help = HelpWriting.objects.first()
        article.helps.add(an_help)
        article.save()

        response = self.client.get(
            reverse('content:helps'),
            follow=False
        )
        self.assertEqual(200, response.status_code)
        contents = response.context['contents']
        self.assertEqual(len(contents), 2)  # ... then this time, we get two results !

        response = self.client.get(
            reverse('content:helps') +
            u'?need={}'.format(an_help.slug),
            follow=False
        )
        self.assertEqual(200, response.status_code)
        contents = response.context['contents']
        self.assertEqual(len(contents), 2)  # same with the help

        response = self.client.get(
            reverse('content:helps') +
            u'?need={}'.format(HelpWriting.objects.last().slug),
            follow=False
        )
        self.assertEqual(200, response.status_code)
        contents = response.context['contents']
        self.assertEqual(len(contents), 1)  # but only one if we ask for another need

        # test "type" filter:
        response = self.client.get(
            reverse('content:helps') +
            u'?type=article',
            follow=False
        )
        self.assertEqual(200, response.status_code)
        contents = response.context['contents']
        self.assertEqual(len(contents), 1)

        response = self.client.get(
            reverse('content:helps') +
            u'?type=tuto',
            follow=False
        )
        self.assertEqual(200, response.status_code)
        contents = response.context['contents']
        self.assertEqual(len(contents), 1)

        # test pagination page doesn't exist
        response = self.client.get(
            reverse('content:helps') +
            u'?page=1534',
            follow=False
        )
        self.assertEqual(404, response.status_code)

        # test pagination page not an integer
        response = self.client.get(
            reverse('content:helps') +
            u'?page=abcd',
            follow=False
        )
        self.assertEqual(404, response.status_code)

    def test_add_author(self):
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)
        result = self.client.post(
            reverse('content:add-author', args=[self.tuto.pk]),
            {
                'username': self.user_guest.username
            },
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(PublishableContent.objects.get(pk=self.tuto.pk).authors.count(), 2)
        gallery = UserGallery.objects.filter(gallery=self.tuto.gallery, user=self.user_guest).first()
        self.assertIsNotNone(gallery)
        self.assertEqual(GALLERY_WRITE, gallery.mode)
        # add unexisting user
        result = self.client.post(
            reverse('content:add-author', args=[self.tuto.pk]),
            {
                'username': "unknown"
            },
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(PublishableContent.objects.get(pk=self.tuto.pk).authors.count(), 2)

    def test_remove_author(self):
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)
        tuto = PublishableContentFactory(author_list=[self.user_author, self.user_guest])
        result = self.client.post(
            reverse('content:remove-author', args=[tuto.pk]),
            {
                'username': self.user_guest.username
            },
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(PublishableContent.objects.get(pk=tuto.pk).authors.count(), 1)

        self.assertIsNone(UserGallery.objects.filter(gallery=self.tuto.gallery, user=self.user_guest).first())
        # remove unexisting user
        result = self.client.post(
            reverse('content:add-author', args=[tuto.pk]),
            {
                'username': "unknown"
            },
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(PublishableContent.objects.get(pk=tuto.pk).authors.count(), 1)
        # remove last author must lead to no change
        result = self.client.post(
            reverse('content:add-author', args=[tuto.pk]),
            {
                'username': self.user_author.username
            },
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(PublishableContent.objects.get(pk=tuto.pk).authors.count(), 1)

    def test_warn_typo(self):
        """
        Add a non-regression test about warning the author(s) of a typo in tutorial
        """

        typo_text = u'T\'as fait une faute, t\'es trop nul'

        # create a tuto, populate, and set beta
        tuto = PublishableContentFactory(type='TUTORIAL')
        tuto.authors.add(self.user_author)
        tuto.gallery = GalleryFactory()
        tuto.licence = self.licence
        tuto.subcategory.add(self.subcategory)
        tuto.save()

        versioned = tuto.load_version()
        chapter = ContainerFactory(parent=versioned, db_object=tuto)
        ExtractFactory(container=chapter, db_object=tuto)

        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)

        sha_draft = PublishableContent.objects.get(pk=tuto.pk).sha_draft
        response = self.client.post(
            reverse('content:set-beta', kwargs={'pk': tuto.pk, 'slug': tuto.slug}),
            {
                'version': sha_draft
            },
            follow=False
        )
        self.assertEqual(302, response.status_code)
        sha_beta = PublishableContent.objects.get(pk=tuto.pk).sha_beta
        self.assertEqual(sha_draft, sha_beta)

        tuto = PublishableContent.objects.get(pk=tuto.pk)
        versioned = tuto.load_version()

        # check if author get error when warning typo on its own tutorial
        result = self.client.post(
            reverse('content:warn-typo') + '?pk={}'.format(tuto.pk),
            {
                'pk': tuto.pk,
                'version': sha_beta,
                'text': typo_text,
                'target': ''
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
                username=self.user_guest.username,
                password='hostel77'),
            True)

        # check if user can warn typo in tutorial
        result = self.client.post(
            reverse('content:warn-typo') + '?pk={}'.format(tuto.pk),
            {
                'pk': tuto.pk,
                'version': sha_beta,
                'text': typo_text,
                'target': ''
            },
            follow=True)
        self.assertEqual(result.status_code, 200)

        msgs = result.context['messages']
        last = None
        for msg in msgs:
            last = msg
        self.assertEqual(last.level, messages.SUCCESS)

        # check PM :
        sent_pm = PrivateTopic.objects.filter(author=self.user_guest.pk).last()
        self.assertIn(self.user_author, sent_pm.participants.all())  # author is in participants
        self.assertIn(typo_text, sent_pm.last_message.text)  # typo is in message
        self.assertIn(versioned.get_absolute_url_beta(), sent_pm.last_message.text)  # beta url is in message

        # check if user can warn typo in chapter of tutorial
        chapter = versioned.children[-1]
        result = self.client.post(
            reverse('content:warn-typo') + '?pk={}'.format(tuto.pk),
            {
                'pk': tuto.pk,
                'version': sha_beta,
                'text': typo_text,
                'target': chapter.get_path(relative=True)
            },
            follow=True)
        self.assertEqual(result.status_code, 200)

        msgs = result.context['messages']
        last = None
        for msg in msgs:
            last = msg
        self.assertEqual(last.level, messages.SUCCESS)

        # check PM :
        sent_pm = PrivateTopic.objects.filter(author=self.user_guest.pk).last()
        self.assertIn(self.user_author, sent_pm.participants.all())  # author is in participants
        self.assertIn(typo_text, sent_pm.last_message.text)  # typo is in message
        self.assertIn(chapter.get_absolute_url_beta(), sent_pm.last_message.text)  # beta url is in message

        # now, induce change and publish
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)

        ExtractFactory(container=chapter, db_object=tuto)  # new extract

        tuto = PublishableContent.objects.get(pk=tuto.pk)
        versioned = tuto.load_version()

        # ask validation
        self.assertEqual(Validation.objects.count(), 0)

        result = self.client.post(
            reverse('validation:ask', kwargs={'pk': tuto.pk, 'slug': tuto.slug}),
            {
                'text': u'valide moi ça, please',
                'source': '',
                'version': versioned.current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        # login with staff and publish
        self.assertEqual(
            self.client.login(
                username=self.user_staff.username,
                password='hostel77'),
            True)

        validation = Validation.objects.filter(content=tuto).last()

        result = self.client.post(
            reverse('validation:reserve', kwargs={'pk': validation.pk}),
            {
                'version': validation.version
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        # accept
        result = self.client.post(
            reverse('validation:accept', kwargs={'pk': validation.pk}),
            {
                'text': u'ça m\'as l\'air nul, mais je valide',
                'is_major': True,
                'source': u''
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        published = PublishedContent.objects.filter(content=tuto).first()
        self.assertIsNotNone(published)

        # now, same stuffs on the public version
        tuto = PublishableContent.objects.get(pk=tuto.pk)
        versioned = tuto.load_version()

        self.assertEqual(
            self.client.login(
                username=self.user_guest.username,
                password='hostel77'),
            True)

        # check if user can warn typo in tutorial
        result = self.client.post(
            reverse('content:warn-typo') + '?pk={}'.format(tuto.pk),
            {
                'pk': tuto.pk,
                'version': tuto.sha_public,
                'text': typo_text,
                'target': ''
            },
            follow=True)
        self.assertEqual(result.status_code, 200)

        msgs = result.context['messages']
        last = None
        for msg in msgs:
            last = msg
        self.assertEqual(last.level, messages.SUCCESS)

        # check PM :
        sent_pm = PrivateTopic.objects.filter(author=self.user_guest.pk).last()
        self.assertIn(self.user_author, sent_pm.participants.all())  # author is in participants
        self.assertIn(typo_text, sent_pm.last_message.text)  # typo is in message
        self.assertIn(versioned.get_absolute_url_online(), sent_pm.last_message.text)  # online url is in message

        # check if user can warn typo in chapter of tutorial
        result = self.client.post(
            reverse('content:warn-typo') + '?pk={}'.format(tuto.pk),
            {
                'pk': tuto.pk,
                'version': tuto.sha_public,
                'text': typo_text,
                'target': chapter.get_path(relative=True)
            },
            follow=True)
        self.assertEqual(result.status_code, 200)

        msgs = result.context['messages']
        last = None
        for msg in msgs:
            last = msg
        self.assertEqual(last.level, messages.SUCCESS)

        # check PM :
        sent_pm = PrivateTopic.objects.filter(author=self.user_guest.pk).last()
        self.assertIn(self.user_author, sent_pm.participants.all())  # author is in participants
        self.assertIn(typo_text, sent_pm.last_message.text)  # typo is in message
        self.assertIn(versioned.children[0].get_absolute_url_online(), sent_pm.last_message.text)

    def test_concurent_edition(self):
        """ensure that an edition is not successfull without provided the good `last_hash` to each form"""

        # create a tuto and populate
        tuto = PublishableContentFactory(type='TUTORIAL')
        tuto.authors.add(self.user_author)
        tuto.gallery = GalleryFactory()
        tuto.licence = self.licence
        tuto.subcategory.add(self.subcategory)
        tuto.save()

        versioned = tuto.load_version()
        chapter = ContainerFactory(parent=versioned, db_object=tuto)
        extract = ExtractFactory(container=chapter, db_object=tuto)

        random = u'Il est miniuit 30 et j\'écris un test ;)'

        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)

        # no hash, no edition
        result = self.client.post(
            reverse('content:edit', args=[tuto.pk, tuto.slug]),
            {
                'title': tuto.title,
                'description': tuto.description,
                'introduction': random,
                'conclusion': random,
                'type': u'TUTORIAL',
                'licence': self.licence.pk,
                'subcategory': self.subcategory.pk,
                'last_hash': ''
            },
            follow=True)
        self.assertEqual(result.status_code, 200)

        msgs = result.context['messages']
        last = None
        for msg in msgs:
            last = msg
        self.assertEqual(last.level, messages.ERROR)

        tuto = PublishableContent.objects.get(pk=tuto.pk)
        versioned = tuto.load_version()
        self.assertNotEqual(versioned.get_introduction(), random)
        self.assertNotEqual(versioned.get_conclusion(), random)

        result = self.client.post(
            reverse('content:edit', args=[tuto.pk, tuto.slug]),
            {
                'title': tuto.title,
                'description': tuto.description,
                'introduction': random,
                'conclusion': random,
                'type': u'TUTORIAL',
                'licence': self.licence.pk,
                'subcategory': self.subcategory.pk,
                'last_hash': versioned.compute_hash()  # good hash
            },
            follow=True)
        self.assertEqual(result.status_code, 200)

        tuto = PublishableContent.objects.get(pk=tuto.pk)
        versioned = tuto.load_version()
        self.assertEqual(versioned.get_introduction(), random)
        self.assertEqual(versioned.get_conclusion(), random)

        # edit container:
        result = self.client.post(
            reverse('content:edit-container',
                    kwargs={
                        'pk': tuto.pk,
                        'slug': tuto.slug,
                        'container_slug': chapter.slug}),
            {
                'title': chapter.title,
                'introduction': random,
                'conclusion': random,
                'last_hash': ''
            },
            follow=True)
        self.assertEqual(result.status_code, 200)

        msgs = result.context['messages']
        last = None
        for msg in msgs:
            last = msg
        self.assertEqual(last.level, messages.ERROR)

        tuto = PublishableContent.objects.get(pk=tuto.pk)
        chapter_version = tuto.load_version().children[0]
        self.assertNotEqual(chapter_version.get_introduction(), random)
        self.assertNotEqual(chapter_version.get_conclusion(), random)

        result = self.client.post(
            reverse('content:edit-container',
                    kwargs={
                        'pk': tuto.pk,
                        'slug': tuto.slug,
                        'container_slug': chapter.slug}),
            {
                'title': chapter.title,
                'introduction': random,
                'conclusion': random,
                'last_hash': chapter_version.compute_hash()
            },
            follow=True)
        self.assertEqual(result.status_code, 200)

        tuto = PublishableContent.objects.get(pk=tuto.pk)
        chapter_version = tuto.load_version().children[0]
        self.assertEqual(chapter_version.get_introduction(), random)
        self.assertEqual(chapter_version.get_conclusion(), random)

        # edit extract
        result = self.client.post(
            reverse('content:edit-extract',
                    kwargs={
                        'pk': tuto.pk,
                        'slug': tuto.slug,
                        'container_slug': chapter_version.slug,
                        'extract_slug': extract.slug
                    }),
            {
                'title': random,
                'text': random,
                'last_hash': ''
            },
            follow=True)
        self.assertEqual(result.status_code, 200)

        msgs = result.context['messages']
        last = None
        for msg in msgs:
            last = msg
        self.assertEqual(last.level, messages.ERROR)

        versioned = PublishableContent.objects.get(pk=tuto.pk).load_version()
        extract = versioned.children[0].children[0]
        self.assertNotEqual(extract.get_text(), random)

        result = self.client.post(
            reverse('content:edit-extract',
                    kwargs={
                        'pk': tuto.pk,
                        'slug': tuto.slug,
                        'container_slug': chapter_version.slug,
                        'extract_slug': extract.slug
                    }),
            {
                'title': random,
                'text': random,
                'last_hash': extract.compute_hash()
            },
            follow=True)
        self.assertEqual(result.status_code, 200)

        versioned = PublishableContent.objects.get(pk=tuto.pk).load_version()
        extract = versioned.children[0].children[0]
        self.assertEqual(extract.get_text(), random)

    def test_malformed_url(self):
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)

        result = self.client.get(
            self.chapter1.get_absolute_url()[:-2] + "/"
        )
        self.assertEqual(result.status_code, 404)
        result = self.client.get(
            self.part1.get_absolute_url()[:-2] + "/"
        )
        self.assertEqual(result.status_code, 404)
        result = self.client.get(
            self.chapter1.get_absolute_url().replace(str(self.tuto.pk), u"he-s-dead-jim")
        )
        self.assertEqual(result.status_code, 404)
        result = self.client.get(
            self.chapter1.get_absolute_url().replace(str(self.tuto.slug), u"he-s-dead-jim")
        )
        self.assertEqual(result.status_code, 404)
        publishable = PublishedContentFactory(author_list=[self.user_author])
        published = PublishedContent.objects.filter(content_pk=publishable.pk).first()
        result = self.client.get(
            published.get_absolute_url_online().replace(str(published.content_public_slug), u"he-s-dead-jim")
        )
        self.assertEqual(result.status_code, 404)
        result = self.client.get(
            published.get_absolute_url_online().replace(str(published.content.pk), u"1000000000")
        )
        self.assertEqual(result.status_code, 404)
        result = self.client.get(
            published.get_absolute_url_online().replace(str(published.content.pk), u"he-s-dead-jim")
        )
        self.assertEqual(result.status_code, 404)
        self.assertEqual(
            self.client.login(
                username=self.user_guest.username,
                password='hostel77'),
            True)

        result = self.client.post(
            reverse("content:add-reaction") + u'?pk={}'.format(publishable.pk),
            {
                'text': u'message',
                'last_note': '0'
            }, follow=True)

        result = self.client.get(published.get_absolute_url_online() + "?page=2")
        self.assertEqual(result.status_code, 404)
        result = self.client.get(published.get_absolute_url_online() + "?page=clementine")
        self.assertEqual(result.status_code, 404)
        publishable = PublishableContentFactory(author_list=[self.user_author])
        result = self.client.get(publishable.get_absolute_url().replace(str(publishable.pk), "10000"))
        self.assertEqual(result.status_code, 404)
        result = self.client.get(publishable.get_absolute_url().replace(str(publishable.slug), "10000"))
        self.assertEqual(result.status_code, 403)  # get 403 since you're not author

    def test_upvote_downvote(self):
        publishable = PublishedContentFactory(author_list=[self.user_author])
        self.assertEqual(
            self.client.login(
                username=self.user_guest.username,
                password='hostel77'),
            True)

        self.client.post(
            reverse("content:add-reaction") + u'?pk={}'.format(publishable.pk),
            {
                'text': u'message',
                'last_note': '0'
            }, follow=True)

        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)
        reac = ContentReaction.objects.last()
        result = self.client.post(
            reverse("content:up-vote") + "?message=" + str(reac.pk),
            follow=False
        )
        self.assertEqual(result.status_code, 302)
        self.assertEqual(CommentLike.objects.filter(user__pk=self.user_author.pk).count(), 1)
        result = self.client.post(
            reverse("content:up-vote") + "?message=" + str(reac.pk),
            follow=False
        )
        self.assertEqual(result.status_code, 302)
        self.assertEqual(CommentLike.objects.filter(user__pk=self.user_author.pk).count(), 0)
        result = self.client.post(
            reverse("content:up-vote") + "?message=" + str(reac.pk),
            follow=False
        )
        result = self.client.post(
            reverse("content:down-vote") + "?message=" + str(reac.pk),
            follow=False
        )
        self.assertEqual(result.status_code, 302)
        self.assertEqual(CommentLike.objects.filter(user__pk=self.user_author.pk).count(), 0)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(CommentDislike.objects.filter(user__pk=self.user_author.pk).count(), 1)

    def test_hide_reaction(self):
        publishable = PublishedContentFactory(author_list=[self.user_author])
        self.assertEqual(
            self.client.login(
                username=self.user_guest.username,
                password='hostel77'),
            True)

        self.client.post(
            reverse("content:add-reaction") + u'?pk={}'.format(publishable.pk),
            {
                'text': u'message',
                'last_note': '0'
            }, follow=True)
        reaction = ContentReaction.objects.filter(related_content__pk=publishable.pk).first()
        result = self.client.post(reverse('content:hide-reaction', args=[reaction.pk]),
                                  {'text_hidden': u"Ever notice how you come across somebody "
                                                  u"once in a while you shouldn't "
                                                  u"have fucked with? That's me."}, follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertFalse(ContentReaction.objects.filter(related_content__pk=publishable.pk).first().is_visible)

    def test_alert_reaction(self):
        publishable = PublishedContentFactory(author_list=[self.user_author])
        self.assertEqual(
            self.client.login(
                username=self.user_guest.username,
                password='hostel77'),
            True)

        self.client.post(
            reverse("content:add-reaction") + u'?pk={}'.format(publishable.pk),
            {
                'text': u'message',
                'last_note': '0'
            }, follow=True)
        reaction = ContentReaction.objects.filter(related_content__pk=publishable.pk).first()
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)
        result = self.client.post(
            reverse('content:alert-reaction', args=[reaction.pk]),
            {
                "signal_text": 'No. Try not. Do... or do not. There is no try.'
            }, follow=False
        )
        self.assertEqual(result.status_code, 302)
        self.assertIsNotNone(Alert.objects.filter(author__pk=self.user_author.pk, comment__pk=reaction.pk).first())
        result = self.client.post(
            reverse('content:resolve-reaction'),
            {
                "alert_pk": Alert.objects.filter(author__pk=self.user_author.pk, comment__pk=reaction.pk).first().pk,
                "text": 'No. Try not. Do... or do not. There is no try.'
            }, follow=False
        )
        self.assertEqual(result.status_code, 403)
        self.assertEqual(
            self.client.login(
                username=self.user_staff.username,
                password='hostel77'),
            True)
        result = self.client.post(
            reverse('content:resolve-reaction'),
            {
                "alert_pk": Alert.objects.filter(author__pk=self.user_author.pk, comment__pk=reaction.pk).first().pk,
                "text": 'Much to learn, you still have.'
            }, follow=False
        )
        self.assertEqual(result.status_code, 302)
        self.assertIsNone(Alert.objects.filter(author__pk=self.user_author.pk, comment__pk=reaction.pk).first())

    def tearDown(self):

        if os.path.isdir(settings.ZDS_APP['content']['repo_private_path']):
            shutil.rmtree(settings.ZDS_APP['content']['repo_private_path'])
        if os.path.isdir(settings.ZDS_APP['content']['repo_public_path']):
            shutil.rmtree(settings.ZDS_APP['content']['repo_public_path'])
        if os.path.isdir(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)
