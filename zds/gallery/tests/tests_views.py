import os

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from zds.gallery.models import Gallery, Image, UserGallery
from zds.gallery.tests.factories import GalleryFactory, ImageFactory, UserGalleryFactory
from zds.member.tests.factories import ProfileFactory


class GalleryListViewTest(TestCase):
    def test_denies_anonymous(self):
        response = self.client.get(reverse("gallery:list"), follow=True)
        self.assertRedirects(response, reverse("member-login") + "?next=" + reverse("gallery:list"))

    def test_list_galeries_belong_to_member(self):
        profile = ProfileFactory()
        gallery = GalleryFactory()
        GalleryFactory()
        UserGalleryFactory(user=profile.user, gallery=gallery)

        self.client.force_login(profile.user)

        response = self.client.get(reverse("gallery:list"), follow=True)
        self.assertEqual(200, response.status_code)

        self.assertEqual(1, len(response.context["galleries"]))
        self.assertEqual(
            UserGallery.objects.filter(user=profile.user).first().gallery, response.context["galleries"].first()
        )


class GalleryDetailViewTest(TestCase):
    def setUp(self):
        self.profile1 = ProfileFactory()
        self.profile2 = ProfileFactory()

    def test_denies_anonymous(self):
        response = self.client.get(reverse("gallery:details", args=["89", "test-gallery"]), follow=True)
        self.assertRedirects(
            response, reverse("member-login") + "?next=" + reverse("gallery:details", args=["89", "test-gallery"])
        )

    def test_fail_gallery_no_exist(self):
        self.client.force_login(self.profile1.user)
        response = self.client.get(reverse("gallery:details", args=["89", "test-gallery"]), follow=True)

        self.assertEqual(404, response.status_code)

    def test_fail_gallery_details_no_permission(self):
        """fail when a user has no permission at all"""
        gallery = GalleryFactory()
        UserGalleryFactory(gallery=gallery, user=self.profile1.user)

        self.client.force_login(self.profile2.user)

        response = self.client.get(reverse("gallery:details", args=[gallery.pk, gallery.slug]))
        self.assertEqual(403, response.status_code)

    def test_success_gallery_details_permission_authorized(self):
        gallery = GalleryFactory()
        UserGalleryFactory(gallery=gallery, user=self.profile1.user)
        UserGalleryFactory(gallery=gallery, user=self.profile2.user)

        self.client.force_login(self.profile2.user)

        response = self.client.get(reverse("gallery:details", args=[gallery.pk, gallery.slug]))
        self.assertEqual(200, response.status_code)


class NewGalleryViewTest(TestCase):
    def setUp(self):
        self.profile1 = ProfileFactory()

    def test_denies_anonymous(self):
        response = self.client.get(reverse("gallery:create"), follow=True)
        self.assertRedirects(response, reverse("member-login") + "?next=" + reverse("gallery:create"))

        response = self.client.post(reverse("gallery:create"), follow=True)
        self.assertRedirects(response, reverse("member-login") + "?next=" + reverse("gallery:create"))

    def test_access_member(self):
        """just verify with get request that everythings is ok"""
        self.client.force_login(self.profile1.user)

        response = self.client.get(reverse("gallery:create"))
        self.assertEqual(200, response.status_code)

    def test_fail_new_gallery_with_missing_params(self):
        self.client.force_login(self.profile1.user)
        self.assertEqual(0, Gallery.objects.count())

        response = self.client.post(reverse("gallery:create"), {"subtitle": "test"})
        self.assertEqual(200, response.status_code)
        self.assertTrue(response.context["form"].errors)
        self.assertEqual(0, Gallery.objects.filter(subtitle="test").count())

    def test_success_new_gallery(self):
        self.client.force_login(self.profile1.user)
        self.assertEqual(0, Gallery.objects.count())

        response = self.client.post(
            reverse("gallery:create"), {"title": "test title", "subtitle": "test subtitle"}, follow=True
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(2, Gallery.objects.count())

        user_gallery = UserGallery.objects.filter(user=self.profile1.user)
        self.assertEqual(2, user_gallery.count())
        self.assertEqual("test title", user_gallery[0].gallery.title)
        self.assertEqual("test subtitle", user_gallery[0].gallery.subtitle)
        self.assertEqual("W", user_gallery[0].mode)


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
        self.user_gallery3 = UserGalleryFactory(user=self.profile2.user, gallery=self.gallery1, mode="R")
        default_gallery_u1 = GalleryFactory(title="default", slug="default", subtitle="bla")
        UserGalleryFactory(user=self.profile1.user, gallery=default_gallery_u1, is_default=True)
        default_gallery_u2 = GalleryFactory(title="default", slug="default", subtitle="bla")
        UserGalleryFactory(user=self.profile2.user, gallery=default_gallery_u2, is_default=True)

    def tearDown(self):
        self.image1.delete()
        self.image2.delete()
        self.image3.delete()

    def test_fail_delete_multi_read_permission(self):
        """when user wants to delete a list of galleries just with a read permission"""
        self.client.force_login(self.profile2.user)

        self.assertEqual(4, Gallery.objects.all().count())
        self.assertEqual(5, UserGallery.objects.all().count())
        self.assertEqual(3, Image.objects.all().count())

        response = self.client.post(
            reverse("gallery:delete"), {"delete_multi": "", "g_items": [self.gallery1.pk]}, follow=True
        )
        self.assertEqual(200, response.status_code)

        self.assertEqual(4, Gallery.objects.all().count())
        self.assertEqual(5, UserGallery.objects.all().count())
        self.assertEqual(3, Image.objects.all().count())

    def test_success_delete_multi_write_permission(self):
        self.client.force_login(self.profile1.user)

        self.assertEqual(4, Gallery.objects.all().count())
        self.assertEqual(5, UserGallery.objects.all().count())
        self.assertEqual(3, Image.objects.all().count())

        response = self.client.post(
            reverse("gallery:delete"),
            {"delete_multi": "", "g_items": [self.gallery1.pk, self.gallery2.pk]},
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, Gallery.objects.all().count())
        self.assertEqual(2, UserGallery.objects.all().count())
        self.assertEqual(0, Image.objects.all().count())

    def test_fail_delete_read_permission(self):
        """when user wants to delete a gallery just with a read permission"""
        self.client.force_login(self.profile2.user)

        self.assertEqual(4, Gallery.objects.all().count())
        self.assertEqual(5, UserGallery.objects.all().count())
        self.assertEqual(3, Image.objects.all().count())

        response = self.client.post(reverse("gallery:delete"), {"delete": "", "gallery": self.gallery1.pk}, follow=True)
        self.assertEqual(403, response.status_code)

        self.assertEqual(4, Gallery.objects.all().count())
        self.assertEqual(5, UserGallery.objects.all().count())
        self.assertEqual(3, Image.objects.all().count())

    def test_success_delete_write_permission(self):
        self.client.force_login(self.profile1.user)

        self.assertEqual(4, Gallery.objects.all().count())
        self.assertEqual(5, UserGallery.objects.all().count())
        self.assertEqual(3, Image.objects.all().count())

        response = self.client.post(reverse("gallery:delete"), {"delete": "", "gallery": self.gallery1.pk}, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, Gallery.objects.filter(pk=self.gallery1.pk).count())
        self.assertEqual(0, UserGallery.objects.filter(gallery=self.gallery1).count())
        self.assertEqual(0, Image.objects.filter(gallery=self.gallery1).count())

    def test_fail_add_user_with_read_permission(self):
        self.client.force_login(self.profile2.user)

        # gallery nonexistent
        response = self.client.post(
            reverse("gallery:members", kwargs={"pk": 99999}),
            {
                "action": "add",
            },
        )
        self.assertEqual(404, response.status_code)

        # try to add a user with write permission
        response = self.client.post(
            reverse("gallery:members", kwargs={"pk": self.gallery1.pk}),
            {
                "action": "add",
                "user": self.profile2.user.username,
                "mode": "W",
            },
        )
        self.assertEqual(403, response.status_code)

    def test_fail_add_user_already_has_permission(self):
        self.client.force_login(self.profile1.user)

        # Same permission : read
        response = self.client.post(
            reverse("gallery:members", kwargs={"pk": self.gallery1.pk}),
            {
                "action": "add",
                "user": self.profile2.user.username,
                "mode": "R",
            },
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        permissions = UserGallery.objects.filter(user=self.profile2.user, gallery=self.gallery1)
        self.assertEqual(1, len(permissions))
        self.assertEqual("R", permissions[0].mode)

        # try to add write permission to a user
        # who has already an read permission
        response = self.client.post(
            reverse("gallery:members", kwargs={"pk": self.gallery1.pk}),
            {
                "action": "add",
                "user": self.profile2.user.username,
                "mode": "W",
            },
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        permissions = UserGallery.objects.filter(user=self.profile2.user, gallery=self.gallery1)
        self.assertEqual(1, len(permissions))
        self.assertEqual("R", permissions[0].mode)

    def test_success_add_user_read_permission(self):
        self.client.force_login(self.profile1.user)

        response = self.client.post(
            reverse("gallery:members", kwargs={"pk": self.gallery1.pk}),
            {
                "action": "add",
                "user": self.profile3.user.username,
                "mode": "R",
            },
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        permissions = UserGallery.objects.filter(user=self.profile3.user, gallery=self.gallery1)
        self.assertEqual(1, len(permissions))
        self.assertEqual("R", permissions[0].mode)

    def test_success_add_user_write_permission(self):
        self.client.force_login(self.profile1.user)

        response = self.client.post(
            reverse("gallery:members", kwargs={"pk": self.gallery1.pk}),
            {
                "action": "add",
                "user": self.profile3.user.username,
                "mode": "W",
            },
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        permissions = UserGallery.objects.filter(user=self.profile3.user, gallery=self.gallery1)
        self.assertEqual(1, len(permissions))
        self.assertEqual("W", permissions[0].mode)

    def test_success_modify_user_write_permission(self):
        self.client.force_login(self.profile1.user)

        response = self.client.post(
            reverse("gallery:members", kwargs={"pk": self.gallery1.pk}),
            {
                "action": "add",
                "user": self.profile3.user.username,
                "mode": "W",
            },
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        permissions = UserGallery.objects.filter(user=self.profile3.user, gallery=self.gallery1)
        self.assertEqual(1, len(permissions))
        self.assertEqual("W", permissions[0].mode)

        response = self.client.post(
            reverse("gallery:members", kwargs={"pk": self.gallery1.pk}),
            {
                "action": "edit",
                "user": self.profile3.user.username,
                "mode": "R",
            },
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        permissions = UserGallery.objects.filter(user=self.profile3.user, gallery=self.gallery1)
        self.assertEqual(1, len(permissions))
        self.assertEqual("R", permissions[0].mode)

    def test_fail_user_modify_self(self):
        self.client.force_login(self.profile1.user)

        response = self.client.post(
            reverse("gallery:members", kwargs={"pk": self.gallery1.pk}),
            {
                "action": "edit",
                "user": self.profile1.user.username,
                "mode": "R",
            },
            follow=True,
        )
        self.assertEqual(403, response.status_code)
        permissions = UserGallery.objects.filter(user=self.profile1.user, gallery=self.gallery1)
        self.assertEqual(1, len(permissions))
        self.assertEqual("W", permissions[0].mode)

    def test_success_user_leave_gallery(self):
        self.client.force_login(self.profile1.user)

        user_galleries = UserGallery.objects.filter(gallery=self.gallery1)
        self.assertEqual(user_galleries.count(), 2)

        # kick the other
        response = self.client.post(
            reverse("gallery:members", kwargs={"pk": self.gallery1.pk}),
            {
                "action": "leave",
                "user": self.profile2.user.username,
            },
            follow=True,
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(user_galleries.count(), 1)
        self.assertEqual(user_galleries.last().user, self.profile1.user)

    def test_error_last_user_with_write_leave_gallery(self):
        self.client.force_login(self.profile1.user)

        user_gallery = UserGallery.objects.filter(gallery=self.gallery1, user=self.profile1.user)
        self.assertEqual(user_gallery.count(), 1)

        # try to quit
        response = self.client.post(
            reverse("gallery:members", kwargs={"pk": self.gallery1.pk}),
            {
                "action": "leave",
                "user": self.profile1.user.username,
            },
            follow=True,
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(user_gallery.count(), 1)  # not gone

    def test_success_user_with_read_permission_leave_gallery(self):
        self.client.force_login(self.profile2.user)

        user_galleries = UserGallery.objects.filter(gallery=self.gallery1)
        self.assertEqual(user_galleries.count(), 2)

        # leave
        response = self.client.post(
            reverse("gallery:members", kwargs={"pk": self.gallery1.pk}),
            {
                "action": "leave",
                "user": self.profile2.user.username,
            },
            follow=True,
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(user_galleries.count(), 1)
        self.assertEqual(user_galleries.last().user, self.profile1.user)

    def test_fail_user_modify_user_has_permission(self):
        self.client.force_login(self.profile2.user)

        user_galleries = UserGallery.objects.filter(gallery=self.gallery1)
        self.assertEqual(user_galleries.count(), 2)

        # set W
        response = self.client.post(
            reverse("gallery:members", kwargs={"pk": self.gallery1.pk}),
            {
                "action": "edit",
                "user": self.profile2.user.username,
                "mode": "W",
            },
            follow=True,
        )
        self.assertEqual(403, response.status_code)
        permissions = UserGallery.objects.filter(user=self.profile2.user, gallery=self.gallery1)
        self.assertEqual(1, len(permissions))
        self.assertEqual("R", permissions[0].mode)

        # kick other
        response = self.client.post(
            reverse("gallery:members", kwargs={"pk": self.gallery1.pk}),
            {
                "action": "leave",
                "user": self.profile1.user.username,
            },
            follow=True,
        )

        self.assertEqual(403, response.status_code)
        self.assertEqual(user_galleries.count(), 2)


class EditGalleryTestView(TestCase):
    def setUp(self):
        self.profile1 = ProfileFactory()
        self.profile2 = ProfileFactory()
        self.profile3 = ProfileFactory()
        self.gallery1 = GalleryFactory()
        self.user_gallery1 = UserGalleryFactory(user=self.profile1.user, gallery=self.gallery1)
        self.user_gallery3 = UserGalleryFactory(user=self.profile3.user, gallery=self.gallery1, mode="R")

    def test_fail_member_no_permission_can_edit_gallery(self):
        self.client.force_login(self.profile2.user)

        given_title = "Un nouveau titre"
        given_subtile = "Un nouveau sous-titre"

        self.client.post(
            reverse("gallery:edit", args=[self.gallery1.pk]),
            {"title": given_title, "subtitle": given_subtile},
            follow=True,
        )

        gallery = Gallery.objects.get(pk=self.gallery1.pk)
        self.assertNotEqual(given_title, gallery.title)
        self.assertNotEqual(given_subtile, gallery.subtitle)

    def test_fail_member_read_permission_can_edit_gallery(self):
        self.client.force_login(self.profile3.user)

        given_title = "Un nouveau titre"
        given_subtile = "Un nouveau sous-titre"

        self.client.post(
            reverse("gallery:edit", args=[self.gallery1.pk]),
            {"title": given_title, "subtitle": given_subtile},
            follow=True,
        )

        gallery = Gallery.objects.get(pk=self.gallery1.pk)
        self.assertNotEqual(given_title, gallery.title)
        self.assertNotEqual(given_subtile, gallery.subtitle)

    def test_success_member_edit_gallery(self):
        self.client.force_login(self.profile1.user)

        given_title = "Un nouveau titre"
        given_subtile = "Un nouveau sous-titre"

        self.client.post(
            reverse("gallery:edit", args=[self.gallery1.pk]),
            {"title": given_title, "subtitle": given_subtile},
            follow=True,
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
        self.user_gallery1 = UserGalleryFactory(user=self.profile1.user, gallery=self.gallery, mode="W")
        self.user_gallery2 = UserGalleryFactory(user=self.profile2.user, gallery=self.gallery, mode="R")

    def tearDown(self):
        self.image.delete()

    def test_fail_member_no_permission_can_edit_image(self):
        self.client.force_login(self.profile3.user)

        with (settings.BASE_DIR / "fixtures" / "logo.png").open("rb") as fp:
            self.client.post(
                reverse("gallery:image-edit", args=[self.gallery.pk, self.image.pk]),
                {"title": "modify with no perms", "legend": "test legend", "physical": fp},
                follow=True,
            )

        image_test = Image.objects.get(pk=self.image.pk)
        self.assertNotEqual("modify with no perms", image_test.title)
        image_test.delete()

    def test_success_member_edit_image(self):
        self.client.force_login(self.profile1.user)

        for filename in (
            settings.BASE_DIR / "fixtures" / "logo.png",
            settings.BASE_DIR / "assets" / "licenses" / "copyright.svg",
        ):
            with self.subTest(filename):
                nb_files = len(os.listdir(self.gallery.get_gallery_path()))

                with open(filename, "rb") as fp:
                    response = self.client.post(
                        reverse("gallery:image-edit", args=[self.gallery.pk, self.image.pk]),
                        {"title": "edit title", "legend": "dit legend", "physical": fp},
                        follow=True,
                    )
                self.assertEqual(200, response.status_code)
                # Check that 1 image and 2 thumbnails have been saved in the gallery
                self.assertEqual(nb_files + 3, len(os.listdir(self.gallery.get_gallery_path())))

                self.image.refresh_from_db()
                self.assertEqual("edit title", self.image.title)

    def test_access_permission(self):
        self.client.force_login(self.profile1.user)

        response = self.client.get(reverse("gallery:image-edit", args=[self.gallery.pk, self.image.pk]))

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
        self.user_gallery3 = UserGalleryFactory(user=self.profile2.user, gallery=self.gallery1, mode="R")

    def tearDown(self):
        self.image1.delete()
        self.image2.delete()
        self.image3.delete()

    def test_fail_modify_image_with_no_permission(self):
        self.client.force_login(self.profile3.user)

        response = self.client.post(
            reverse("gallery:image-delete", kwargs={"pk_gallery": self.gallery1.pk}),
            {
                "gallery": self.gallery1.pk,
            },
            follow=True,
        )
        self.assertTrue(403, response.status_code)

    def test_delete_image_from_other_user(self):
        """if user try to remove images from another user without permission"""
        profile4 = ProfileFactory()
        gallery4 = GalleryFactory()
        image4 = ImageFactory(gallery=gallery4)
        UserGalleryFactory(user=profile4.user, gallery=gallery4)
        self.assertEqual(1, Image.objects.filter(pk=image4.pk).count())

        self.client.force_login(self.profile1.user)

        self.client.post(
            reverse("gallery:image-delete", kwargs={"pk_gallery": self.gallery1.pk}),
            {"gallery": self.gallery1.pk, "delete": "", "image": image4.pk},
            follow=True,
        )

        self.assertEqual(1, Image.objects.filter(pk=image4.pk).count())
        image4.delete()

    def test_success_delete_image_write_permission(self):
        self.client.force_login(self.profile1.user)
        nb_files = len(os.listdir(self.gallery1.get_gallery_path()))

        response = self.client.post(
            reverse("gallery:image-delete", kwargs={"pk_gallery": self.gallery1.pk}),
            {"gallery": self.gallery1.pk, "delete": "", "image": self.image1.pk},
            follow=True,
        )
        self.assertEqual(200, response.status_code)

        self.assertEqual(0, Image.objects.filter(pk=self.image1.pk).count())

        # picture AND thumbnails should be gone
        self.assertEqual(nb_files, len(os.listdir(self.gallery1.get_gallery_path())))

    def test_success_delete_list_images_write_permission(self):
        self.client.force_login(self.profile1.user)

        response = self.client.post(
            reverse("gallery:image-delete", kwargs={"pk_gallery": self.gallery1.pk}),
            {"gallery": self.gallery1.pk, "delete_multi": "", "g_items": [self.image1.pk, self.image2.pk]},
            follow=True,
        )
        self.assertEqual(200, response.status_code)

        self.assertEqual(0, Image.objects.filter(pk=self.image1.pk).count())
        self.assertEqual(0, Image.objects.filter(pk=self.image2.pk).count())

    def test_fail_delete_image_read_permission(self):
        self.client.force_login(self.profile2.user)

        response = self.client.post(
            reverse("gallery:image-delete", kwargs={"pk_gallery": self.gallery1.pk}),
            {"gallery": self.gallery1.pk, "delete": "", "image": self.image1.pk},
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
        self.user_gallery1 = UserGalleryFactory(user=self.profile1.user, gallery=self.gallery, mode="W")
        self.user_gallery2 = UserGalleryFactory(user=self.profile2.user, gallery=self.gallery, mode="R")

    def test_success_new_image_write_permission(self):
        self.client.force_login(self.profile1.user)
        self.assertEqual(0, len(self.gallery.get_images()))

        for filename in (
            settings.BASE_DIR / "fixtures" / "logo.png",
            settings.BASE_DIR / "assets" / "licenses" / "copyright.svg",
        ):
            with self.subTest(filename):
                with open(filename, "rb") as fp:
                    response = self.client.post(
                        reverse("gallery:image-add", args=[self.gallery.pk]),
                        {"title": "Test title", "legend": "Test legend", "physical": fp},
                        follow=True,
                    )

                self.assertEqual(200, response.status_code)
                self.assertEqual(1, len(self.gallery.get_images()))
                self.assertEqual(3, len(os.listdir(self.gallery.get_gallery_path())))  # New image and thumbnail
                self.gallery.get_images()[0].delete()

    def test_fail_new_image_with_read_permission(self):
        self.client.force_login(self.profile2.user)
        self.assertEqual(0, len(self.gallery.get_images()))

        with (settings.BASE_DIR / "fixtures" / "logo.png").open("rb") as fp:
            response = self.client.post(
                reverse("gallery:image-add", args=[self.gallery.pk]),
                {"title": "Test title", "legend": "Test legend", "physical": fp},
                follow=True,
            )

        self.assertEqual(403, response.status_code)
        self.assertEqual(0, len(self.gallery.get_images()))

    def test_fail_new_image_with_no_permission(self):
        self.client.force_login(self.profile3.user)
        self.assertEqual(0, len(self.gallery.get_images()))

        with (settings.BASE_DIR / "fixtures" / "logo.png").open("rb") as fp:
            response = self.client.post(
                reverse("gallery:image-add", args=[self.gallery.pk]),
                {"title": "Test title", "legend": "Test legend", "physical": fp},
                follow=True,
            )

        self.assertEqual(403, response.status_code)
        self.assertEqual(0, len(self.gallery.get_images()))

    def test_fail_gallery_not_exist(self):
        self.client.force_login(self.profile1.user)

        with (settings.BASE_DIR / "fixtures" / "logo.png").open("rb") as fp:
            response = self.client.post(
                reverse("gallery:image-add", args=[156]),
                {"title": "Test title", "legend": "Test legend", "physical": fp},
                follow=True,
            )

        self.assertEqual(404, response.status_code)

    def test_import_images_in_gallery(self):
        self.client.force_login(self.profile1.user)

        with (settings.BASE_DIR / "fixtures" / "archive-gallery.zip").open("rb") as fp:
            response = self.client.post(
                reverse("gallery:image-import", args=[self.gallery.pk]), {"file": fp}, follow=False
            )
        self.assertEqual(302, response.status_code)
        img = self.gallery.get_images()[0]
        self.assertEqual(Image.objects.filter(gallery=self.gallery).count(), 1)
        self.assertEqual("jpg", img.get_extension())
        response = self.client.post(
            reverse("gallery:image-delete", kwargs={"pk_gallery": self.gallery.pk}),
            {"delete": "", "image": img.pk},
            follow=True,
        )
        self.assertEqual(200, response.status_code)

    def test_import_images_in_gallery_no_archive(self):
        self.client.force_login(self.profile1.user)

        with (settings.BASE_DIR / "fixtures" / "archive-gallery.zip").open("rb"):
            response = self.client.post(
                reverse("gallery:image-import", args=[self.gallery.pk]),
                {
                    # normally we have
                    # 'file': fp
                    # but here we want to act as if we forgot it
                },
                follow=False,
            )
        self.assertEqual(200, response.status_code)
        self.assertEqual(Image.objects.filter(gallery=self.gallery).count(), 0)

    def test_denies_import_images_in_gallery(self):
        self.client.force_login(self.profile2.user)

        with (settings.BASE_DIR / "fixtures" / "archive-gallery.zip").open("rb") as fp:
            response = self.client.post(
                reverse("gallery:image-import", args=[self.gallery.pk]), {"file": fp}, follow=True
            )
        self.assertEqual(403, response.status_code)
        self.assertEqual(Image.objects.filter(gallery=self.gallery).count(), 0)
