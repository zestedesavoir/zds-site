#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib
import os

from django.test import TestCase, Client
from django.core.urlresolvers import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from zds.member.factories import ProfileFactory, StaffProfileFactory
from zds.gallery.factories import GalleryFactory, UserGalleryFactory, ImageFactory
from zds.gallery.models import Gallery, UserGallery, Image
from zds import settings


class GalleryListViewTest(TestCase):

    def test_denies_anonymous(self):
        response = self.client.get(reverse('zds.gallery.views.gallery_list'), follow=True)
        self.assertRedirects(response,
                reverse('zds.member.views.login_view')
                +'?next='+urllib.quote(reverse('zds.gallery.views.gallery_list'), ''))

    def test_member_access(self):
        member = ProfileFactory()
        login_check = self.client.login(
                username=member.user.username,
                password='hostel77'
        )
        self.assertTrue(login_check)

        response = self.client.get(reverse('zds.gallery.views.gallery_list'), follow=True)
        self.assertEqual(200, response.status_code)

    def test_staff_access(self):
        staff = StaffProfileFactory()
        login_check = self.client.login(
                username=staff.user.username,
                password='hostel77'
        )
        self.assertTrue(login_check)

        response = self.client.get(reverse('zds.gallery.views.gallery_list'), follow=True)
        self.assertEqual(200, response.status_code)

class GalleryDetailViewTest(TestCase):

    def test_denies_anonymous(self):
        response = self.client.get(reverse('zds.gallery.views.gallery_details',
            args=['89', 'test-gallery']), follow=True)
        self.assertRedirects(response,
                reverse('zds.member.views.login_view')
                +'?next='+urllib.quote(reverse('zds.gallery.views.gallery_details',
                    args=['89', 'test-gallery']), ''))

    def test_fail_gallery_no_exist(self):
        profile = ProfileFactory()
        login_check = self.client.login(username=profile.user.username, password='hostel77')
        self.assertTrue(login_check)
        response = self.client.get(reverse('zds.gallery.views.gallery_details',
            args=['89', 'test-gallery']), follow=True)

        self.assertEqual(404, response.status_code)

    def test_fail_gallery_read_permission_denied(self):
        profile1 = ProfileFactory()
        profile2 = ProfileFactory()
        gallery = GalleryFactory()
        user_gallery = UserGalleryFactory(gallery=gallery, user=profile1.user)

        login_check = self.client.login(username=profile2.user.username, password='hostel77')
        self.assertTrue(login_check)

        response = self.client.get(reverse('zds.gallery.views.gallery_details',
            args=[gallery.pk, gallery.slug]))
        self.assertEqual(403, response.status_code)

    def test_success_gallery_read_permission_authorized(self):
        profile1 = ProfileFactory()
        profile2 = ProfileFactory()
        gallery = GalleryFactory()
        user_gallery = UserGalleryFactory(gallery=gallery, user=profile1.user)
        user_gallery = UserGalleryFactory(gallery=gallery, user=profile2.user)

        login_check = self.client.login(username=profile2.user.username, password='hostel77')
        self.assertTrue(login_check)

        response = self.client.get(reverse('zds.gallery.views.gallery_details',
            args=[gallery.pk, gallery.slug]))
        self.assertEqual(200, response.status_code)


class NewGalleryViewTest(TestCase):

    def test_denies_anonymous(self):
        response = self.client.get(reverse('zds.gallery.views.new_gallery'), follow=True)
        self.assertRedirects(response,
                reverse('zds.member.views.login_view')+
                '?next='+
                urllib.quote(reverse('zds.gallery.views.new_gallery'), ''))

        response = self.client.post(reverse('zds.gallery.views.new_gallery'), follow=True)
        self.assertRedirects(response,
                reverse('zds.member.views.login_view')+
                '?next='+
                urllib.quote(reverse('zds.gallery.views.new_gallery'), ''))

    def test_access_member(self):
        profile = ProfileFactory()
        login_check = self.client.login(username=profile.user.username, password='hostel77')
        self.assertTrue(login_check)

        response = self.client.get(reverse('zds.gallery.views.new_gallery'))
        self.assertEqual(200, response.status_code)


    def test_fail_new_gallery(self):
        profile = ProfileFactory()
        login_check = self.client.login(username=profile.user.username, password='hostel77')
        self.assertTrue(login_check)
        self.assertEqual(0, Gallery.objects.count())

        response = self.client.post(reverse('zds.gallery.views.new_gallery'), {
            'subtitle': 'test'})
        self.assertEqual(200, response.status_code)
        self.assertTrue(response.context['form'].errors)
        self.assertEqual(0, Gallery.objects.count())

    def test_success_new_gallery(self):
        profile = ProfileFactory()
        login_check = self.client.login(username=profile.user.username, password='hostel77')
        self.assertTrue(login_check)
        self.assertEqual(0, Gallery.objects.count())

        response = self.client.post(reverse('zds.gallery.views.new_gallery'), {
            'title': 'test title', 'subtitle': 'test subtitle'}, follow=True)

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, Gallery.objects.count())

        user_gallery = UserGallery.objects.filter(user=profile.user)
        self.assertEqual(1, user_gallery.count())
        self.assertEqual('test title', user_gallery[0].gallery.title)
        self.assertEqual('test subtitle', user_gallery[0].gallery.subtitle)
        self.assertEqual('W', user_gallery[0].mode)


class ModifyGalleryViewTest(TestCase):

    def setUp(self):
        self.profile1 = ProfileFactory()
        self.profile2 = ProfileFactory()
        self.profile3 = ProfileFactory()
        self.gallery1 = GalleryFactory()
        self.gallery2 = GalleryFactory()
        self.image1 = ImageFactory(gallery=self.gallery1)
        self.image2 = ImageFactory(gallery=self.gallery1)
        self.image3 = ImageFactory(gallery=self.gallery2)
        self.user_gallery1 = UserGalleryFactory(user=self.profile1.user, gallery=self.gallery1)
        self.user_gallery2 = UserGalleryFactory(user=self.profile1.user, gallery=self.gallery2)
        self.user_gallery3 = UserGalleryFactory(user=self.profile2.user, gallery=self.gallery1, mode='R')

    def tearDown(self):
        self.image1.delete()
        self.image2.delete()

    def test_fail_delete_multi_read_permission(self):
        login_check = self.client.login(username=self.profile2.user.username, password='hostel77')
        self.assertTrue(login_check)

        self.assertEqual(2, Gallery.objects.all().count())
        self.assertEqual(3, UserGallery.objects.all().count())
        self.assertEqual(3, Image.objects.all().count())

        response = self.client.post(
                reverse('zds.gallery.views.modify_gallery'),
                {
                    'delete_multi':'',
                    'items': [self.gallery1.pk]
                },
                follow=True
        )
        self.assertEqual(403, response.status_code)

        self.assertEqual(2, Gallery.objects.all().count())
        self.assertEqual(3, UserGallery.objects.all().count())
        self.assertEqual(3, Image.objects.all().count())

    def test_success_delete_multi_write_permission(self):
        login_check = self.client.login(username=self.profile1.user.username, password='hostel77')
        self.assertTrue(login_check)

        self.assertEqual(2, Gallery.objects.all().count())
        self.assertEqual(3, UserGallery.objects.all().count())
        self.assertEqual(3, Image.objects.all().count())

        response = self.client.post(
                reverse('zds.gallery.views.modify_gallery'),
                {
                    'delete_multi':'',
                    'items': [self.gallery1.pk, self.gallery2.pk]
                },
                follow=True
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, Gallery.objects.all().count())
        self.assertEqual(0, UserGallery.objects.all().count())
        self.assertEqual(0, Image.objects.all().count())

    def test_fail_add_user_read_permission(self):
        login_check = self.client.login(username=self.profile2.user.username, password='hostel77')
        self.assertTrue(login_check)

        response = self.client.post(
                reverse('zds.gallery.views.modify_gallery'),
                {
                    'adduser':'',
                    'gallery': 89,
                }
        )
        self.assertEqual(404, response.status_code)

        response = self.client.post(
                reverse('zds.gallery.views.modify_gallery'),
                {
                    'adduser':'',
                    'gallery': self.gallery1.pk,
                    'user': self.profile2.user.username,
                    'mode': 'W',
                }
        )
        self.assertEqual(403, response.status_code)

    def test_fail_add_user_already_has_permission(self):
        login_check = self.client.login(username=self.profile1.user.username, password='hostel77')
        self.assertTrue(login_check)

        # Same permission : read
        response = self.client.post(
                reverse('zds.gallery.views.modify_gallery'),
                {
                    'adduser':'',
                    'gallery': self.gallery1.pk,
                    'user': self.profile2.user.username,
                    'mode': 'R',
                },
                follow=True
        )
        self.assertEqual(200, response.status_code)
        permissions = UserGallery.objects.filter(user=self.profile2.user, gallery=self.gallery1)
        self.assertEqual(1, len(permissions))
        self.assertEqual('R', permissions[0].mode)

    def test_success_add_user_read_permission(self):
        login_check = self.client.login(username=self.profile1.user.username, password='hostel77')
        self.assertTrue(login_check)

        response = self.client.post(
                reverse('zds.gallery.views.modify_gallery'),
                {
                    'adduser':'',
                    'gallery': self.gallery1.pk,
                    'user': self.profile3.user.username,
                    'mode': 'R',
                },
                follow=True
        )
        self.assertEqual(200, response.status_code)
        permissions = UserGallery.objects.filter(user=self.profile3.user, gallery=self.gallery1)
        self.assertEqual(1, len(permissions))
        self.assertEqual('R', permissions[0].mode)

    def test_success_add_user_write_permission(self):
        login_check = self.client.login(username=self.profile1.user.username, password='hostel77')
        self.assertTrue(login_check)

        response = self.client.post(
                reverse('zds.gallery.views.modify_gallery'),
                {
                    'adduser':'',
                    'gallery': self.gallery1.pk,
                    'user': self.profile3.user.username,
                    'mode': 'W',
                },
                follow=True
        )
        self.assertEqual(200, response.status_code)
        permissions = UserGallery.objects.filter(user=self.profile3.user, gallery=self.gallery1)
        self.assertEqual(1, len(permissions))
        self.assertEqual('W', permissions[0].mode)


class EditImageViewTest(TestCase):

    def setUp(self):
        self.gallery = GalleryFactory()
        self.image = ImageFactory(gallery=self.gallery)
        self.profile1 = ProfileFactory()
        self.profile2 = ProfileFactory()
        self.profile3 = ProfileFactory()
        self.user_gallery1 = UserGalleryFactory(user=self.profile1.user, gallery=self.gallery, mode='W')
        self.user_gallery2 = UserGalleryFactory(user=self.profile2.user, gallery=self.gallery, mode='R')

    def tearDown(self):
        self.image.delete()

    def test_fail_member_no_permission_edit_image(self):
        login_check = self.client.login(username=self.profile3.user.username, password='hostel77')
        self.assertTrue(login_check)

        with open(os.path.join(settings.SITE_ROOT, 'fixtures', 'logo.png'), 'r') as fp:

            response = self.client.post(
                    reverse(
                        'zds.gallery.views.edit_image',
                        args=[self.gallery.pk, self.image.pk]
                    ),
                    {
                        'title': 'modify with no perms',
                        'legend': 'test legend',
                        'slug': 'test-slug',
                        'physical': fp
                    },
                    follow=True
            )

        image_test = Image.objects.get(pk=self.image.pk)
        self.assertNotEqual('modify with no perms', image_test.title)

    def test_success_member_edit_image(self):
        login_check = self.client.login(username=self.profile1.user.username, password='hostel77')
        self.assertTrue(login_check)

        with open(os.path.join(settings.SITE_ROOT, 'fixtures', 'logo.png'), 'r') as fp:

            response = self.client.post(
                    reverse(
                        'zds.gallery.views.edit_image',
                        args=[self.gallery.pk, self.image.pk]
                    ),
                    {
                        'title': 'edit title',
                        'legend': 'dit legend',
                        'slug': 'edit-slug',
                        'physical': fp
                    },
                    follow=True
            )

        self.assertEqual(200, response.status_code)
        image_test = Image.objects.get(pk=self.image.pk)
        self.assertEqual('edit title', image_test.title)

    def test_access_permission(self):
        login_check = self.client.login(username=self.profile1.user.username, password='hostel77')
        self.assertTrue(login_check)

        response = self.client.get(reverse(
            'zds.gallery.views.edit_image',
            args=[self.gallery.pk, self.image.pk]
        ))

        self.assertEqual(200, response.status_code)


class ModifyImageTest(TestCase):

    def setUp(self):
        self.profile1 = ProfileFactory()
        self.profile2 = ProfileFactory()
        self.profile3 = ProfileFactory()
        self.gallery1 = GalleryFactory()
        self.gallery2 = GalleryFactory()
        self.image1 = ImageFactory(gallery=self.gallery1)
        self.image2 = ImageFactory(gallery=self.gallery1)
        self.image3 = ImageFactory(gallery=self.gallery2)
        self.user_gallery1 = UserGalleryFactory(user=self.profile1.user, gallery=self.gallery1)
        self.user_gallery2 = UserGalleryFactory(user=self.profile1.user, gallery=self.gallery2)
        self.user_gallery3 = UserGalleryFactory(user=self.profile2.user, gallery=self.gallery1, mode='R')

    def tearDown(self):
        self.image1.delete()
        self.image2.delete()

    def test_fail_modify_image_no_permission(self):
        login_check = self.client.login(username=self.profile3.user.username, password='hostel77')
        self.assertTrue(login_check)

        response = self.client.post(
                reverse('zds.gallery.views.modify_image'),
                {
                    'gallery': self.gallery1.pk,
                },
                follow=True,
        )
        self.assertTrue(403, response.status_code)

    def test_delete_image_from_other_user(self):
        profile4 = ProfileFactory()
        gallery4 = GalleryFactory()
        image4 = ImageFactory(gallery=gallery4)
        user_gallery = UserGalleryFactory(user=profile4.user, gallery=gallery4)
        self.assertEqual(1, Image.objects.filter(pk=image4.pk).count())

        login_check = self.client.login(username=self.profile1.user.username, password='hostel77')
        self.assertTrue(login_check)

        response = self.client.post(
                reverse('zds.gallery.views.modify_image'),
                {
                    'gallery': self.gallery1.pk,
                    'delete': '',
                    'image': image4.pk
                },
                follow=True,
        )

        self.assertEqual(1, Image.objects.filter(pk=image4.pk).count())



    def test_success_delete_image_write_permission(self):
        login_check = self.client.login(username=self.profile1.user.username, password='hostel77')
        self.assertTrue(login_check)

        response = self.client.post(
                reverse('zds.gallery.views.modify_image'),
                {
                    'gallery': self.gallery1.pk,
                    'delete': '',
                    'image': self.image1.pk
                },
                follow=True,
        )
        self.assertEqual(200, response.status_code)

        self.assertEqual(0, Image.objects.filter(pk=self.image1.pk).count())

    def test_success_delete_list_images_write_permission(self):
        login_check = self.client.login(username=self.profile1.user.username, password='hostel77')
        self.assertTrue(login_check)

        response = self.client.post(
                reverse('zds.gallery.views.modify_image'),
                {
                    'gallery': self.gallery1.pk,
                    'delete_multi': '',
                    'items': [self.image1.pk, self.image2.pk]
                },
                follow=True,
        )
        self.assertEqual(200, response.status_code)

        self.assertEqual(0, Image.objects.filter(pk=self.image1.pk).count())
        self.assertEqual(0, Image.objects.filter(pk=self.image2.pk).count())


    def test_fail_delete_image_read_permission(self):
        login_check = self.client.login(username=self.profile2.user.username, password='hostel77')
        self.assertTrue(login_check)

        response = self.client.post(
                reverse('zds.gallery.views.modify_image'),
                {
                    'gallery': self.gallery1.pk,
                    'delete': '',
                    'image': self.image1.pk
                },
                follow=True,
        )
        self.assertEqual(403, response.status_code)

        self.assertEqual(1, Image.objects.filter(pk=self.image1.pk).count())


class NewImageViewTest(TestCase):

    def setUp(self):
        self.gallery = GalleryFactory()
        self.profile1 = ProfileFactory()
        self.profile2 = ProfileFactory()
        self.profile3 = ProfileFactory()
        self.user_gallery1 = UserGalleryFactory(user=self.profile1.user, gallery=self.gallery, mode='W')
        self.user_gallery2 = UserGalleryFactory(user=self.profile2.user, gallery=self.gallery, mode='R')

    def test_success_new_image_write_permission(self):
        login_check = self.client.login(username=self.profile1.user.username, password='hostel77')
        self.assertTrue(login_check)
