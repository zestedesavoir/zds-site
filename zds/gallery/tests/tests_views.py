#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib
import os

from django.test import TestCase
from django.core.urlresolvers import reverse

from zds.member.factories import ProfileFactory
from zds.gallery.factories import GalleryFactory, UserGalleryFactory, ImageFactory
from zds.gallery.models import Gallery, UserGallery, Image
from zds import settings


class GalleryListViewTest(TestCase):

    def test_denies_anonymous(self):
        response = self.client.get(reverse('gallery-list'), follow=True)
        self.assertRedirects(response,
                             reverse('member-login') +
                             '?next=' + urllib.quote(reverse('gallery-list'), ''))

    def test_list_galeries_belong_to_member(self):
        profile = ProfileFactory()
        gallery = GalleryFactory()
        GalleryFactory()
        UserGalleryFactory(user=profile.user, gallery=gallery)

        login_check = self.client.login(
            username=profile.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)

        response = self.client.get(reverse('gallery-list'), follow=True)
        self.assertEqual(200, response.status_code)

        self.assertEqual(1, len(response.context['galleries']))
        self.assertEqual(UserGallery.objects.filter(user=profile.user)[0], response.context['galleries'][0][0])


class GalleryDetailViewTest(TestCase):

    def setUp(self):
        self.profile1 = ProfileFactory()
        self.profile2 = ProfileFactory()

    def test_denies_anonymous(self):
        response = self.client.get(reverse('gallery-details',
                                           args=['89', 'test-gallery']), follow=True)
        self.assertRedirects(response,
                             reverse('member-login') +
                             '?next=' + urllib.quote(reverse('gallery-details',
                                                             args=['89', 'test-gallery']), ''))

    def test_fail_gallery_no_exist(self):
        login_check = self.client.login(username=self.profile1.user.username, password='hostel77')
        self.assertTrue(login_check)
        response = self.client.get(reverse('gallery-details',
                                           args=['89', 'test-gallery']), follow=True)

        self.assertEqual(404, response.status_code)

    def test_fail_gallery_details_no_permission(self):
        """ fail when a user has no permission at all """
        gallery = GalleryFactory()
        UserGalleryFactory(gallery=gallery, user=self.profile1.user)

        login_check = self.client.login(username=self.profile2.user.username, password='hostel77')
        self.assertTrue(login_check)

        response = self.client.get(reverse('gallery-details',
                                           args=[gallery.pk, gallery.slug]))
        self.assertEqual(403, response.status_code)

    def test_success_gallery_details_permission_authorized(self):
        gallery = GalleryFactory()
        UserGalleryFactory(gallery=gallery, user=self.profile1.user)
        UserGalleryFactory(gallery=gallery, user=self.profile2.user)

        login_check = self.client.login(username=self.profile2.user.username, password='hostel77')
        self.assertTrue(login_check)

        response = self.client.get(reverse('gallery-details',
                                           args=[gallery.pk, gallery.slug]))
        self.assertEqual(200, response.status_code)


class NewGalleryViewTest(TestCase):

    def setUp(self):
        self.profile1 = ProfileFactory()

    def test_denies_anonymous(self):
        response = self.client.get(reverse('gallery-new'), follow=True)
        self.assertRedirects(response,
                             reverse('member-login') +
                             '?next=' +
                             urllib.quote(reverse('gallery-new'), ''))

        response = self.client.post(reverse('gallery-new'), follow=True)
        self.assertRedirects(response,
                             reverse('member-login') +
                             '?next=' +
                             urllib.quote(reverse('gallery-new'), ''))

    def test_access_member(self):
        """ just verify with get request that everythings is ok """
        login_check = self.client.login(username=self.profile1.user.username, password='hostel77')
        self.assertTrue(login_check)

        response = self.client.get(reverse('gallery-new'))
        self.assertEqual(200, response.status_code)

    def test_fail_new_gallery_with_missing_params(self):
        login_check = self.client.login(username=self.profile1.user.username, password='hostel77')
        self.assertTrue(login_check)
        self.assertEqual(0, Gallery.objects.count())

        response = self.client.post(reverse('gallery-new'), {
            'subtitle': 'test'})
        self.assertEqual(200, response.status_code)
        self.assertTrue(response.context['form'].errors)
        self.assertEqual(0, Gallery.objects.count())

    def test_success_new_gallery(self):
        login_check = self.client.login(username=self.profile1.user.username, password='hostel77')
        self.assertTrue(login_check)
        self.assertEqual(0, Gallery.objects.count())

        response = self.client.post(reverse('gallery-new'), {
            'title': 'test title', 'subtitle': 'test subtitle'}, follow=True)

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, Gallery.objects.count())

        user_gallery = UserGallery.objects.filter(user=self.profile1.user)
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
        self.image3.delete()

    def test_fail_delete_multi_read_permission(self):
        """ when user wants to delete a list of galleries just with a read permission """
        login_check = self.client.login(username=self.profile2.user.username, password='hostel77')
        self.assertTrue(login_check)

        self.assertEqual(2, Gallery.objects.all().count())
        self.assertEqual(3, UserGallery.objects.all().count())
        self.assertEqual(3, Image.objects.all().count())

        response = self.client.post(
            reverse('gallery-modify'),
            {
                'delete_multi': '',
                'g_items': [self.gallery1.pk]
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
            reverse('gallery-modify'),
            {
                'delete_multi': '',
                'g_items': [self.gallery1.pk, self.gallery2.pk]
            },
            follow=True
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, Gallery.objects.all().count())
        self.assertEqual(0, UserGallery.objects.all().count())
        self.assertEqual(0, Image.objects.all().count())

    def test_fail_add_user_with_read_permission(self):
        login_check = self.client.login(username=self.profile2.user.username, password='hostel77')
        self.assertTrue(login_check)

        # gallery nonexistent
        response = self.client.post(
            reverse('gallery-modify'),
            {
                'adduser': '',
                'gallery': 89,
            }
        )
        self.assertEqual(404, response.status_code)

        # try to add an user with write permission
        response = self.client.post(
            reverse('gallery-modify'),
            {
                'adduser': '',
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
            reverse('gallery-modify'),
            {
                'adduser': '',
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

        # try to add write permission to an user
        # who has already an read permission
        response = self.client.post(
            reverse('gallery-modify'),
            {
                'adduser': '',
                'gallery': self.gallery1.pk,
                'user': self.profile2.user.username,
                'mode': 'W',
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
            reverse('gallery-modify'),
            {
                'adduser': '',
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
            reverse('gallery-modify'),
            {
                'adduser': '',
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


class EditGalleryTestView(TestCase):
    def setUp(self):
        self.profile1 = ProfileFactory()
        self.profile2 = ProfileFactory()
        self.profile3 = ProfileFactory()
        self.gallery1 = GalleryFactory()
        self.user_gallery1 = UserGalleryFactory(user=self.profile1.user, gallery=self.gallery1)
        self.user_gallery3 = UserGalleryFactory(user=self.profile3.user, gallery=self.gallery1, mode='R')

    def test_fail_member_no_permission_can_edit_gallery(self):
        login_check = self.client.login(username=self.profile2.user.username, password='hostel77')
        self.assertTrue(login_check)

        given_title = 'Un nouveau titre'
        given_subtile = 'Un nouveau sous-titre'

        self.client.post(
            reverse(
                'gallery-edit',
                args=[self.gallery1.pk, self.gallery1.slug]
            ),
            {
                'title': given_title,
                'subtitle': given_subtile
            },
            follow=True
        )

        gallery = Gallery.objects.get(pk=self.gallery1.pk)
        self.assertNotEqual(given_title, gallery.title)
        self.assertNotEqual(given_subtile, gallery.subtitle)

    def test_fail_member_read_permission_can_edit_gallery(self):
        login_check = self.client.login(username=self.profile3.user.username, password='hostel77')
        self.assertTrue(login_check)

        given_title = 'Un nouveau titre'
        given_subtile = 'Un nouveau sous-titre'

        self.client.post(
            reverse(
                'gallery-edit',
                args=[self.gallery1.pk, self.gallery1.slug]
            ),
            {
                'title': given_title,
                'subtitle': given_subtile
            },
            follow=True
        )

        gallery = Gallery.objects.get(pk=self.gallery1.pk)
        self.assertNotEqual(given_title, gallery.title)
        self.assertNotEqual(given_subtile, gallery.subtitle)

    def test_success_member_edit_gallery(self):
        login_check = self.client.login(username=self.profile1.user.username, password='hostel77')
        self.assertTrue(login_check)

        given_title = 'Un nouveau titre'
        given_subtile = 'Un nouveau sous-titre'

        self.client.post(
            reverse(
                'gallery-edit',
                args=[self.gallery1.pk, self.gallery1.slug]
            ),
            {
                'title': given_title,
                'subtitle': given_subtile
            },
            follow=True
        )

        gallery = Gallery.objects.get(pk=self.gallery1.pk)
        self.assertEqual(given_title, gallery.title)
        self.assertEqual(given_subtile, gallery.subtitle)


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

    def test_denies_anonymous(self):
        response = self.client.get(
            reverse(
                'gallery-image-edit',
                args=[15, 156]
            ),
            follow=True
        )
        self.assertRedirects(response,
                             reverse('member-login') +
                             '?next=' + urllib.quote(reverse('gallery-image-edit', args=[15, 156]), ''))

    def test_fail_member_no_permission_can_edit_image(self):
        login_check = self.client.login(username=self.profile3.user.username, password='hostel77')
        self.assertTrue(login_check)

        with open(os.path.join(settings.BASE_DIR, 'fixtures', 'logo.png'), 'r') as fp:

            self.client.post(
                reverse(
                    'gallery-image-edit',
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
        image_test.delete()

    def test_success_member_edit_image(self):
        login_check = self.client.login(username=self.profile1.user.username, password='hostel77')
        self.assertTrue(login_check)

        nb_files = len(os.listdir(self.gallery.get_gallery_path()))

        with open(os.path.join(settings.BASE_DIR, 'fixtures', 'logo.png'), 'r') as fp:

            response = self.client.post(
                reverse(
                    'gallery-image-edit',
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
        self.assertEqual(nb_files + 3, len(os.listdir(self.gallery.get_gallery_path())))

        image_test = Image.objects.get(pk=self.image.pk)
        self.assertEqual('edit title', image_test.title)
        image_test.delete()
        # picture AND thumbnail should be gone
        self.assertEqual(nb_files, len(os.listdir(self.gallery.get_gallery_path())))

    def test_access_permission(self):
        login_check = self.client.login(username=self.profile1.user.username, password='hostel77')
        self.assertTrue(login_check)

        response = self.client.get(reverse(
            'gallery-image-edit',
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
        self.image3.delete()

    def test_denies_anonymous(self):
        response = self.client.get(reverse('gallery-image-delete'), follow=True)
        self.assertRedirects(response,
                             reverse('member-login') +
                             '?next=' + urllib.quote(reverse('gallery-image-delete'), ''))

    def test_fail_modify_image_with_no_permission(self):
        login_check = self.client.login(username=self.profile3.user.username, password='hostel77')
        self.assertTrue(login_check)

        response = self.client.post(
            reverse('gallery-image-delete'),
            {
                'gallery': self.gallery1.pk,
            },
            follow=True,
        )
        self.assertTrue(403, response.status_code)

    def test_delete_image_from_other_user(self):
        """ if user try to remove images from another user without permission"""
        profile4 = ProfileFactory()
        gallery4 = GalleryFactory()
        image4 = ImageFactory(gallery=gallery4)
        UserGalleryFactory(user=profile4.user, gallery=gallery4)
        self.assertEqual(1, Image.objects.filter(pk=image4.pk).count())

        login_check = self.client.login(username=self.profile1.user.username, password='hostel77')
        self.assertTrue(login_check)

        self.client.post(
            reverse('gallery-image-delete'),
            {
                'gallery': self.gallery1.pk,
                'delete': '',
                'image': image4.pk
            },
            follow=True,
        )

        self.assertEqual(1, Image.objects.filter(pk=image4.pk).count())
        image4.delete()

    def test_success_delete_image_write_permission(self):
        login_check = self.client.login(username=self.profile1.user.username, password='hostel77')
        self.assertTrue(login_check)

        response = self.client.post(
            reverse('gallery-image-delete'),
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
            reverse('gallery-image-delete'),
            {
                'gallery': self.gallery1.pk,
                'delete_multi': '',
                'g_items': [self.image1.pk, self.image2.pk]
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
            reverse('gallery-image-delete'),
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

    def test_denies_anonymous(self):
        response = self.client.get(reverse('gallery-image-new', args=[1]), follow=True)
        self.assertRedirects(response,
                             reverse('member-login') +
                             '?next=' + urllib.quote(reverse('gallery-image-new', args=[1]), ''))

    def test_success_new_image_write_permission(self):
        login_check = self.client.login(username=self.profile1.user.username, password='hostel77')
        self.assertTrue(login_check)
        self.assertEqual(0, len(self.gallery.get_images()))

        with open(os.path.join(settings.BASE_DIR, 'fixtures', 'logo.png'), 'r') as fp:
            response = self.client.post(
                reverse(
                    'gallery-image-new',
                    args=[self.gallery.pk]
                ),
                {
                    'title': 'Test title',
                    'legend': 'Test legend',
                    'slug': 'test-slug',
                    'physical': fp
                },
                follow=True
            )

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(self.gallery.get_images()))
        self.assertEqual(3, len(os.listdir(self.gallery.get_gallery_path())))  # New image and thumbnail
        self.gallery.get_images()[0].delete()

    def test_fail_new_image_with_read_permission(self):
        login_check = self.client.login(username=self.profile2.user.username, password='hostel77')
        self.assertTrue(login_check)
        self.assertEqual(0, len(self.gallery.get_images()))

        with open(os.path.join(settings.BASE_DIR, 'fixtures', 'logo.png'), 'r') as fp:
            response = self.client.post(
                reverse(
                    'gallery-image-new',
                    args=[self.gallery.pk]
                ),
                {
                    'title': 'Test title',
                    'legend': 'Test legend',
                    'slug': 'test-slug',
                    'physical': fp
                },
                follow=True
            )

        self.assertEqual(403, response.status_code)
        self.assertEqual(0, len(self.gallery.get_images()))

    def test_fail_new_image_with_no_permission(self):
        login_check = self.client.login(username=self.profile3.user.username, password='hostel77')
        self.assertTrue(login_check)
        self.assertEqual(0, len(self.gallery.get_images()))

        with open(os.path.join(settings.BASE_DIR, 'fixtures', 'logo.png'), 'r') as fp:
            response = self.client.post(
                reverse(
                    'gallery-image-new',
                    args=[self.gallery.pk]
                ),
                {
                    'title': 'Test title',
                    'legend': 'Test legend',
                    'slug': 'test-slug',
                    'physical': fp
                },
                follow=True
            )

        self.assertEqual(403, response.status_code)
        self.assertEqual(0, len(self.gallery.get_images()))

    def test_fail_gallery_not_exist(self):
        login_check = self.client.login(username=self.profile1.user.username, password='hostel77')
        self.assertTrue(login_check)

        with open(os.path.join(settings.BASE_DIR, 'fixtures', 'logo.png'), 'r') as fp:
            response = self.client.post(
                reverse(
                    'gallery-image-new',
                    args=[156]
                ),
                {
                    'title': 'Test title',
                    'legend': 'Test legend',
                    'slug': 'test-slug',
                    'physical': fp
                },
                follow=True
            )

        self.assertEqual(404, response.status_code)

    def test_import_images_in_gallery(self):
        login_check = self.client.login(username=self.profile1.user.username, password='hostel77')
        self.assertTrue(login_check)

        with open(os.path.join(settings.BASE_DIR, 'fixtures', 'archive-gallery.zip'), 'r') as fp:
            response = self.client.post(
                reverse(
                    'gallery-image-import',
                    args=[self.gallery.pk]
                ),
                {
                    'file': fp
                },
                follow=False
            )
        self.assertEqual(302, response.status_code)
        img = self.gallery.get_images()[0]
        self.assertEqual(Image.objects.filter(gallery=self.gallery).count(), 1)
        self.assertEqual('jpg', img.get_extension())
        response = self.client.post(
            reverse('gallery-image-delete'),
            {
                'gallery': self.gallery.pk,
                'delete': '',
                'image': img.pk
            },
            follow=True,
        )
        self.assertEqual(200, response.status_code)

    def test_import_images_in_gallery_no_archive(self):
        login_check = self.client.login(username=self.profile1.user.username, password='hostel77')
        self.assertTrue(login_check)

        with open(os.path.join(settings.BASE_DIR, 'fixtures', 'archive-gallery.zip'), 'r'):
            response = self.client.post(
                reverse(
                    'gallery-image-import',
                    args=[self.gallery.pk]
                ),
                {
                    # normally we have
                    # 'file': fp
                    # but here we want to act as if we forgot it
                },
                follow=False
            )
        self.assertEqual(200, response.status_code)
        self.assertEqual(Image.objects.filter(gallery=self.gallery).count(), 0)

    def test_denies_import_images_in_gallery(self):
        login_check = self.client.login(username=self.profile2.user.username, password='hostel77')
        self.assertTrue(login_check)

        with open(os.path.join(settings.BASE_DIR, 'fixtures', 'archive-gallery.zip'), 'r') as fp:
            response = self.client.post(
                reverse(
                    'gallery-image-import',
                    args=[self.gallery.pk]
                ),
                {
                    'file': fp
                },
                follow=True
            )
        self.assertEqual(403, response.status_code)
        self.assertEqual(Image.objects.filter(gallery=self.gallery).count(), 0)
