# coding: utf-8

import os
import shutil

from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings
from django.core.urlresolvers import reverse

from zds.settings import SITE_ROOT
from zds.member.factories import ProfileFactory, StaffProfileFactory
from zds.tutorialv2.factories import PublishableContentFactory, ContainerFactory, ExtractFactory, LicenceFactory, \
    SubCategoryFactory
from zds.tutorialv2.models import PublishableContent
from zds.gallery.factories import GalleryFactory

overrided_zds_app = settings.ZDS_APP
overrided_zds_app['content']['repo_private_path'] = os.path.join(SITE_ROOT, 'contents-private-test')
overrided_zds_app['content']['repo_public_path'] = os.path.join(SITE_ROOT, 'contents-public-test')


@override_settings(MEDIA_ROOT=os.path.join(SITE_ROOT, 'media-test'))
@override_settings(ZDS_APP=overrided_zds_app)
class ContentTests(TestCase):

    def setUp(self):
        settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
        self.mas = ProfileFactory().user
        settings.ZDS_APP['member']['bot_account'] = self.mas.username

        self.licence = LicenceFactory()
        self.subcategory = SubCategoryFactory()

        self.user_author = ProfileFactory().user
        self.staff = StaffProfileFactory().user
        self.guest = ProfileFactory().user

        self.tuto = PublishableContentFactory(type='TUTORIAL')
        self.tuto.authors.add(self.user_author)
        self.tuto.gallery = GalleryFactory()
        self.tuto.licence = self.licence
        self.tuto.save()

        self.tuto_draft = self.tuto.load_version()
        self.part1 = ContainerFactory(parent=self.tuto_draft, db_object=self.tuto)
        self.chapter1 = ContainerFactory(parent=self.part1, db_object=self.tuto)

        self.extract1 = ExtractFactory(container=self.chapter1, db_object=self.tuto)

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
                username=self.guest.username,
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
                username=self.staff.username,
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
        result = self.client.post(
            reverse('content:edit-container', kwargs={'pk': pk, 'slug': slug, 'container_slug': container.slug}),
            {
                'title': random,
                'introduction': random,
                'conclusion': random
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        versioned = PublishableContent.objects.get(pk=pk).load_version()
        container = versioned.children[0]
        self.assertEqual(container.title, random)
        self.assertEqual(container.get_introduction(), random)
        self.assertEqual(container.get_conclusion(), random)

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
                'conclusion': random
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        versioned = PublishableContent.objects.get(pk=pk).load_version()
        subcontainer = versioned.children[0].children[0]
        self.assertEqual(subcontainer.title, random)
        self.assertEqual(subcontainer.get_introduction(), random)
        self.assertEqual(subcontainer.get_conclusion(), random)

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
                'text': random
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        versioned = PublishableContent.objects.get(pk=pk).load_version()
        extract = versioned.children[0].children[0].children[0]
        self.assertEqual(extract.title, random)
        self.assertEqual(extract.get_text(), random)

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

    def tearDown(self):
        if os.path.isdir(settings.ZDS_APP['content']['repo_private_path']):
            shutil.rmtree(settings.ZDS_APP['content']['repo_private_path'])
        if os.path.isdir(settings.ZDS_APP['content']['repo_public_path']):
            shutil.rmtree(settings.ZDS_APP['content']['repo_public_path'])
        if os.path.isdir(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)
