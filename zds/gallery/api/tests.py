import os
from uuid import uuid4

from django.conf import settings
from django.core.cache import caches
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_extensions.settings import extensions_api_settings

from zds.api.utils import authenticate_oauth2_client
from zds.gallery.models import GALLERY_READ, GALLERY_WRITE, Gallery, Image, UserGallery
from zds.gallery.tests.factories import GalleryFactory, ImageFactory, UserGalleryFactory
from zds.member.tests.factories import ProfileFactory
from zds.tutorialv2.tests import TutorialTestMixin, override_for_contents
from zds.tutorialv2.tests.factories import PublishableContentFactory


class GalleryListAPITest(APITestCase):
    def setUp(self):
        self.profile = ProfileFactory()
        self.client = APIClient()
        authenticate_oauth2_client(self.client, self.profile.user, "hostel77")

        caches[extensions_api_settings.DEFAULT_USE_CACHE].clear()

    def test_get_list_of_gallery_empty(self):
        response = self.client.get(reverse("api:gallery:list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), 0)
        self.assertEqual(response.data.get("results"), [])
        self.assertIsNone(response.data.get("next"))
        self.assertIsNone(response.data.get("previous"))

    def test_get_list_of_gallery(self):
        gallery = GalleryFactory()
        UserGalleryFactory(user=self.profile.user, gallery=gallery)
        response = self.client.get(reverse("api:gallery:list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), 1)
        self.assertIsNone(response.data.get("next"))
        self.assertIsNone(response.data.get("previous"))

    def test_post_create_gallery(self):
        title = "Ma super galerie"
        subtitle = "Comment que ça va être bien"

        response = self.client.post(reverse("api:gallery:list"), {"title": title, "subtitle": subtitle})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Gallery.objects.count(), 1)
        self.assertEqual(UserGallery.objects.count(), 1)

        gallery = Gallery.objects.first()
        self.assertEqual(gallery.title, title)
        self.assertEqual(gallery.subtitle, subtitle)

        user_gallery = UserGallery.objects.first()
        self.assertEqual(user_gallery.user, self.profile.user)
        self.assertEqual(user_gallery.gallery, gallery)
        self.assertEqual(user_gallery.mode, GALLERY_WRITE)

        self.assertEqual(response.data.get("id"), gallery.pk)
        self.assertEqual(response.data.get("title"), gallery.title)
        self.assertEqual(response.data.get("subtitle"), gallery.subtitle)
        self.assertIsNone(response.data.get("linked_content"))
        self.assertEqual(response.data.get("image_count"), 0)

    def test_post_create_gallery_no_subtitle(self):
        title = "Ma super galerie"

        response = self.client.post(reverse("api:gallery:list"), {"title": title})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Gallery.objects.count(), 1)
        self.assertEqual(UserGallery.objects.count(), 1)

        gallery = Gallery.objects.first()
        self.assertEqual(gallery.title, title)
        self.assertEqual(gallery.subtitle, "")

        self.assertEqual(response.data.get("title"), gallery.title)
        self.assertEqual(response.data.get("subtitle"), "")


@override_for_contents()
class GalleryDetailAPITest(TutorialTestMixin, APITestCase):
    def setUp(self):
        self.profile = ProfileFactory()
        self.other = ProfileFactory()
        self.client = APIClient()
        authenticate_oauth2_client(self.client, self.profile.user, "hostel77")

        self.gallery = GalleryFactory()

        tuto = PublishableContentFactory(type="TUTORIAL", author_list=[self.profile.user])
        self.gallery_tuto = tuto.gallery

        caches[extensions_api_settings.DEFAULT_USE_CACHE].clear()

    def test_get_gallery(self):
        UserGalleryFactory(user=self.profile.user, gallery=self.gallery)

        response = self.client.get(reverse("api:gallery:detail", kwargs={"pk": self.gallery.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), self.gallery.pk)
        self.assertEqual(response.data.get("title"), self.gallery.title)
        self.assertEqual(response.data.get("subtitle"), self.gallery.subtitle)
        self.assertIsNone(response.data.get("linked_content"))
        self.assertEqual(response.data.get("image_count"), 0)
        self.assertEqual(response.data.get("permissions"), {"read": True, "write": True})

    def test_get_gallery_read_permissions(self):
        UserGalleryFactory(user=self.other.user, gallery=self.gallery)
        UserGalleryFactory(user=self.profile.user, gallery=self.gallery, mode=GALLERY_READ)

        response = self.client.get(reverse("api:gallery:detail", kwargs={"pk": self.gallery.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), self.gallery.pk)
        self.assertEqual(response.data.get("permissions"), {"read": True, "write": False})

    def test_get_gallery_linked_content(self):
        response = self.client.get(reverse("api:gallery:detail", kwargs={"pk": self.gallery_tuto.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), self.gallery_tuto.pk)
        self.assertEqual(response.data.get("permissions"), {"read": True, "write": True})

    def test_get_fail_non_existing(self):
        response = self.client.get(reverse("api:gallery:detail", kwargs={"pk": 99999}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_fail_no_right(self):
        UserGalleryFactory(user=self.other.user, gallery=self.gallery)

        response = self.client.get(reverse("api:gallery:detail", kwargs={"pk": self.gallery.pk}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_put_update_gallery(self):
        title = "Ma super galerie"
        subtitle = "... A été mise à jour !"

        UserGalleryFactory(user=self.profile.user, gallery=self.gallery)

        response = self.client.put(
            reverse("api:gallery:detail", kwargs={"pk": self.gallery.pk}), {"title": title, "subtitle": subtitle}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        gallery = Gallery.objects.get(pk=self.gallery.pk)
        self.assertEqual(gallery.title, title)
        self.assertEqual(gallery.subtitle, subtitle)

        self.assertEqual(response.data.get("title"), gallery.title)
        self.assertEqual(response.data.get("subtitle"), gallery.subtitle)

    def test_put_fail_linked_content(self):
        title = "Ma super galerie?"
        subtitle = "... Appartient à un tuto"

        response = self.client.put(
            reverse("api:gallery:detail", kwargs={"pk": self.gallery_tuto.pk}), {"title": title, "subtitle": subtitle}
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        gallery = Gallery.objects.get(pk=self.gallery_tuto.pk)
        self.assertNotEqual(gallery.title, title)
        self.assertNotEqual(gallery.subtitle, subtitle)

    def test_put_fail_no_right(self):
        title = "Ma super galerie"
        subtitle = "... A été mise à jour !"

        UserGalleryFactory(user=self.other.user, gallery=self.gallery)

        response = self.client.put(
            reverse("api:gallery:detail", kwargs={"pk": self.gallery.pk}), {"title": title, "subtitle": subtitle}
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        gallery = Gallery.objects.get(pk=self.gallery.pk)
        self.assertNotEqual(gallery.title, title)
        self.assertNotEqual(gallery.subtitle, subtitle)

    def test_delete(self):
        UserGalleryFactory(user=self.profile.user, gallery=self.gallery)

        response = self.client.delete(reverse("api:gallery:detail", kwargs={"pk": self.gallery.pk}))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertEqual(Gallery.objects.filter(pk=self.gallery.pk).count(), 0)
        self.assertEqual(UserGallery.objects.filter(gallery=self.gallery).count(), 0)

    def test_delete_fail_no_right(self):
        UserGalleryFactory(user=self.other.user, gallery=self.gallery)

        response = self.client.delete(reverse("api:gallery:detail", kwargs={"pk": self.gallery.pk}))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertEqual(Gallery.objects.filter(pk=self.gallery.pk).count(), 1)
        self.assertEqual(UserGallery.objects.filter(gallery=self.gallery).count(), 1)

    def test_delete_fail_linked_content(self):
        response = self.client.delete(reverse("api:gallery:detail", kwargs={"pk": self.gallery_tuto.pk}))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertEqual(Gallery.objects.filter(pk=self.gallery_tuto.pk).count(), 1)
        self.assertEqual(UserGallery.objects.filter(gallery=self.gallery_tuto).count(), 1)


class ImageListAPITest(APITestCase):
    def setUp(self):
        self.profile = ProfileFactory()
        self.other = ProfileFactory()
        self.client = APIClient()
        authenticate_oauth2_client(self.client, self.profile.user, "hostel77")

        self.gallery = GalleryFactory()
        UserGalleryFactory(user=self.profile.user, gallery=self.gallery)
        self.image = ImageFactory(gallery=self.gallery)

        self.gallery_other = GalleryFactory()
        UserGalleryFactory(user=self.other.user, gallery=self.gallery_other)
        self.image_other = ImageFactory(gallery=self.gallery_other)

        self.gallery_shared = GalleryFactory()
        UserGalleryFactory(user=self.other.user, gallery=self.gallery_shared)
        UserGalleryFactory(user=self.profile.user, gallery=self.gallery_shared, mode=GALLERY_READ)
        self.image_shared = ImageFactory(gallery=self.gallery_shared)

    def test_get_list(self):
        response = self.client.get(reverse("api:gallery:list-images", kwargs={"pk_gallery": self.gallery.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data.get("count"), 1)
        self.assertEqual(response.data.get("results")[0].get("id"), self.image.pk)

    def test_get_list_read_permissions(self):
        response = self.client.get(reverse("api:gallery:list-images", kwargs={"pk_gallery": self.gallery_shared.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data.get("count"), 1)
        self.assertEqual(response.data.get("results")[0].get("id"), self.image_shared.pk)

    def test_get_list_fail_no_permissions(self):
        response = self.client.get(reverse("api:gallery:list-images", kwargs={"pk_gallery": self.gallery_other.pk}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_add_image(self):
        title = "un super titre pour une image"
        legend = "une super legende aussi"

        response = self.client.post(
            reverse("api:gallery:list-images", kwargs={"pk_gallery": self.gallery.pk}),
            {
                "title": title,
                "legend": legend,
                "physical": (settings.BASE_DIR / "fixtures" / "noir_black.png").open("rb"),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Image.objects.filter(gallery=self.gallery).count(), 2)

        image = Image.objects.filter(gallery=self.gallery).order_by("pk").last()
        self.assertEqual(image.title, title)
        self.assertEqual(image.legend, legend)

    def test_post_fail_add_image_not_an_image(self):
        title = "un super titre pour une image"
        legend = "une super legende aussi"
        filename = str(uuid4()) + ".svgz"
        # generate a bare empty file so that the test continues and sends error message
        with open(filename, "w"):
            pass
        try:
            response = self.client.post(
                reverse("api:gallery:list-images", kwargs={"pk_gallery": self.gallery.pk}),
                {
                    "title": title,
                    "legend": legend,
                    "physical": open(filename, "rb"),
                },
                format="multipart",
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(Image.objects.filter(gallery=self.gallery).count(), 1)
        finally:
            os.remove(filename)

    def test_post_can_add_image_svg_image(self):
        title = "un super titre pour une image svg"
        legend = "une super legende aussi"

        response = self.client.post(
            reverse("api:gallery:list-images", kwargs={"pk_gallery": self.gallery.pk}),
            {
                "title": title,
                "legend": legend,
                "physical": (settings.BASE_DIR / "assets" / "licenses" / "0.svg").open("rb"),
            },
            format="multipart",
        )
        self.assertEqual(Image.objects.filter(gallery=self.gallery).count(), 2)

        image = Image.objects.filter(gallery=self.gallery).order_by("pk").last()
        self.assertEqual(image.title, title)
        self.assertEqual(image.legend, legend)

    def test_post_fail_add_image_no_permissions(self):
        title = "un super titre pour une image"
        legend = "une super legende aussi"

        response = self.client.post(
            reverse("api:gallery:list-images", kwargs={"pk_gallery": self.gallery_other.pk}),
            {
                "title": title,
                "legend": legend,
                "physical": (settings.BASE_DIR / "fixtures" / "noir_black.png").open("rb"),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Image.objects.filter(gallery=self.gallery_other).count(), 1)

    def test_post_fail_add_image_read_permissions(self):
        title = "un super titre pour une image"
        legend = "une super legende aussi"

        response = self.client.post(
            reverse("api:gallery:list-images", kwargs={"pk_gallery": self.gallery_shared.pk}),
            {
                "title": title,
                "legend": legend,
                "physical": (settings.BASE_DIR / "fixtures" / "noir_black.png").open("rb"),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Image.objects.filter(gallery=self.gallery_shared).count(), 1)


class ImageDetailAPITest(APITestCase):
    def setUp(self):
        self.profile = ProfileFactory()
        self.other = ProfileFactory()
        self.client = APIClient()
        authenticate_oauth2_client(self.client, self.profile.user, "hostel77")

        self.gallery = GalleryFactory()
        UserGalleryFactory(user=self.profile.user, gallery=self.gallery)
        self.image = ImageFactory(gallery=self.gallery)

        self.gallery_other = GalleryFactory()
        UserGalleryFactory(user=self.other.user, gallery=self.gallery_other)
        self.image_other = ImageFactory(gallery=self.gallery_other)

        self.gallery_shared = GalleryFactory()
        UserGalleryFactory(user=self.other.user, gallery=self.gallery_shared)
        UserGalleryFactory(user=self.profile.user, gallery=self.gallery_shared, mode=GALLERY_READ)
        self.image_shared = ImageFactory(gallery=self.gallery_shared)

    def test_get_image(self):
        response = self.client.get(
            reverse("api:gallery:detail-image", kwargs={"pk_gallery": self.gallery.pk, "pk": self.image.pk})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data.get("id"), self.image.pk)
        self.assertEqual(response.data.get("title"), self.image.title)
        self.assertEqual(response.data.get("legend"), self.image.legend)
        self.assertEqual(response.data.get("slug"), self.image.slug)
        self.assertEqual(response.data.get("thumbnail"), self.image.get_thumbnail_url())
        self.assertEqual(response.data.get("url"), self.image.get_absolute_url())
        self.assertEqual(response.data.get("permissions"), {"read": True, "write": True})

    def test_get_image_read_permissions(self):
        response = self.client.get(
            reverse(
                "api:gallery:detail-image", kwargs={"pk_gallery": self.gallery_shared.pk, "pk": self.image_shared.pk}
            )
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data.get("id"), self.image_shared.pk)
        self.assertEqual(response.data.get("permissions"), {"read": True, "write": False})

    def test_get_image_fail_permissions(self):
        response = self.client.get(
            reverse("api:gallery:detail-image", kwargs={"pk_gallery": self.gallery_other.pk, "pk": self.image_other.pk})
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_put_modify_image(self):
        title = "un super titre pour une super image"
        legend = "as-tu vu ma légende?"

        response = self.client.put(
            reverse("api:gallery:detail-image", kwargs={"pk_gallery": self.gallery.pk, "pk": self.image.pk}),
            {
                "title": title,
                "legend": legend,
                "physical": (settings.BASE_DIR / "fixtures" / "noir_black.png").open("rb"),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        image = Image.objects.get(pk=self.image.pk)
        self.assertEqual(image.title, title)
        self.assertEqual(image.legend, legend)

    def test_put_fail_modify_image_not_an_image(self):
        title = "un super titre pour une super image"
        legend = "en vrai je peux pas"

        response = self.client.put(
            reverse("api:gallery:detail-image", kwargs={"pk_gallery": self.gallery.pk, "pk": self.image.pk}),
            {
                "title": title,
                "legend": legend,
                "physical": (settings.BASE_DIR / "assets" / "licenses" / "0.svg").open("rb"),
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        image = Image.objects.get(pk=self.image.pk)
        self.assertNotEqual(image.title, title)
        self.assertNotEqual(image.legend, legend)

    def test_put_fail_modify_image_no_permissions(self):
        title = "un super titre pour une super image"
        legend = "en vrai je peux pas"

        response = self.client.put(
            reverse(
                "api:gallery:detail-image", kwargs={"pk_gallery": self.gallery_other.pk, "pk": self.image_other.pk}
            ),
            {"title": title, "legend": legend},
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_put_fail_modify_image_read_permissions(self):
        title = "un super titre pour une super image"
        legend = "en vrai je peux toujours pas :p"

        response = self.client.put(
            reverse(
                "api:gallery:detail-image", kwargs={"pk_gallery": self.gallery_shared.pk, "pk": self.image_shared.pk}
            ),
            {"title": title, "legend": legend},
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_image(self):
        response = self.client.delete(
            reverse("api:gallery:detail-image", kwargs={"pk_gallery": self.gallery.pk, "pk": self.image.pk})
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Image.objects.filter(gallery=self.gallery).count(), 0)

    def test_delete_image_fail_no_permissions(self):
        response = self.client.delete(
            reverse("api:gallery:detail-image", kwargs={"pk_gallery": self.gallery_other.pk, "pk": self.image_other.pk})
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Image.objects.filter(gallery=self.gallery_other).count(), 1)

    def test_delete_image_fail_read_permissions(self):
        response = self.client.delete(
            reverse(
                "api:gallery:detail-image", kwargs={"pk_gallery": self.gallery_shared.pk, "pk": self.image_shared.pk}
            )
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Image.objects.filter(gallery=self.gallery_shared).count(), 1)


@override_for_contents()
class ParticipantListAPITest(TutorialTestMixin, APITestCase):
    def setUp(self):
        self.profile = ProfileFactory()
        self.other = ProfileFactory()
        self.client = APIClient()
        self.new_participant = ProfileFactory()
        authenticate_oauth2_client(self.client, self.profile.user, "hostel77")

        self.gallery = GalleryFactory()
        UserGalleryFactory(user=self.profile.user, gallery=self.gallery)
        self.image = ImageFactory(gallery=self.gallery)

        self.gallery_other = GalleryFactory()
        UserGalleryFactory(user=self.other.user, gallery=self.gallery_other)
        self.image_other = ImageFactory(gallery=self.gallery_other)

        self.gallery_shared = GalleryFactory()
        UserGalleryFactory(user=self.other.user, gallery=self.gallery_shared)
        UserGalleryFactory(user=self.profile.user, gallery=self.gallery_shared, mode=GALLERY_READ)
        self.image_shared = ImageFactory(gallery=self.gallery_shared)

        tuto = PublishableContentFactory(type="TUTORIAL", author_list=[self.profile.user])
        self.gallery_tuto = tuto.gallery

    def test_get_list(self):
        response = self.client.get(reverse("api:gallery:list-participants", kwargs={"pk_gallery": self.gallery.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data.get("count"), 1)
        self.assertEqual(response.data.get("results")[0].get("id"), self.profile.user.pk)

    def test_get_list_linked_content(self):
        response = self.client.get(
            reverse("api:gallery:list-participants", kwargs={"pk_gallery": self.gallery_tuto.pk})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data.get("count"), 1)
        self.assertEqual(response.data.get("results")[0].get("id"), self.profile.user.pk)

    def test_get_list_read_permissions(self):
        response = self.client.get(
            reverse("api:gallery:list-participants", kwargs={"pk_gallery": self.gallery_shared.pk})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), 2)

    def test_get_list_fail_no_permissions(self):
        response = self.client.get(
            reverse("api:gallery:list-participants", kwargs={"pk_gallery": self.gallery_other.pk})
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_add_participant(self):
        response = self.client.post(
            reverse("api:gallery:list-participants", kwargs={"pk_gallery": self.gallery.pk}),
            {"id": self.new_participant.user.pk, "can_write": False},
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserGallery.objects.filter(gallery=self.gallery).count(), 2)

        user_gallery = UserGallery.objects.filter(gallery=self.gallery, user=self.new_participant.user).get()
        self.assertEqual(user_gallery.mode, GALLERY_READ)

    def test_post_fail_add_participant_already_in(self):
        user_gallery = UserGalleryFactory(user=self.new_participant.user, gallery=self.gallery, mode=GALLERY_READ)

        response = self.client.post(
            reverse("api:gallery:list-participants", kwargs={"pk_gallery": self.gallery.pk}),
            {"id": self.new_participant.user.pk, "can_write": True},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        user_gallery = UserGallery.objects.get(pk=user_gallery.pk)
        self.assertEqual(user_gallery.mode, GALLERY_READ)

    def test_post_fail_add_participant_linked_content(self):
        response = self.client.post(
            reverse("api:gallery:list-participants", kwargs={"pk_gallery": self.gallery_tuto.pk}),
            {"id": self.new_participant.user.pk, "can_write": False},
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            UserGallery.objects.filter(gallery=self.gallery_tuto, user=self.new_participant.user).count(), 0
        )

    def test_post_fail_add_participant_no_permissions(self):
        response = self.client.post(
            reverse("api:gallery:list-participants", kwargs={"pk_gallery": self.gallery_other.pk}),
            {"id": self.new_participant.user.pk, "can_write": False},
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            UserGallery.objects.filter(gallery=self.gallery_other, user=self.new_participant.user).count(), 0
        )

    def test_post_fail_add_participant_read_permissions(self):
        response = self.client.post(
            reverse("api:gallery:list-participants", kwargs={"pk_gallery": self.gallery_shared.pk}),
            {"id": self.new_participant.user.pk, "can_write": False},
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            UserGallery.objects.filter(gallery=self.gallery_shared, user=self.new_participant.user).count(), 0
        )


@override_for_contents()
class ParticipantDetailAPITest(TutorialTestMixin, APITestCase):
    def setUp(self):
        self.profile = ProfileFactory()
        self.other = ProfileFactory()
        self.new_participant = ProfileFactory()
        self.client = APIClient()
        authenticate_oauth2_client(self.client, self.profile.user, "hostel77")

        self.gallery = GalleryFactory()
        UserGalleryFactory(user=self.profile.user, gallery=self.gallery)
        self.image = ImageFactory(gallery=self.gallery)

        self.gallery_other = GalleryFactory()
        UserGalleryFactory(user=self.other.user, gallery=self.gallery_other)
        self.image_other = ImageFactory(gallery=self.gallery_other)

        self.gallery_shared = GalleryFactory()
        UserGalleryFactory(user=self.other.user, gallery=self.gallery_shared)
        UserGalleryFactory(user=self.profile.user, gallery=self.gallery_shared, mode=GALLERY_READ)
        self.image_shared = ImageFactory(gallery=self.gallery_shared)

        tuto = PublishableContentFactory(type="TUTORIAL", author_list=[self.profile.user, self.new_participant.user])
        self.gallery_tuto = tuto.gallery

    def test_get_participant(self):
        response = self.client.get(
            reverse(
                "api:gallery:detail-participant",
                kwargs={"pk_gallery": self.gallery.pk, "user__pk": self.profile.user.pk},
            )
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data.get("id"), self.profile.user.pk)
        self.assertEqual(response.data.get("permissions"), {"read": True, "write": True})

    def test_get_participant_linked_content(self):
        response = self.client.get(
            reverse(
                "api:gallery:detail-participant",
                kwargs={"pk_gallery": self.gallery_tuto.pk, "user__pk": self.new_participant.user.pk},
            )
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data.get("id"), self.new_participant.user.pk)
        self.assertEqual(response.data.get("permissions"), {"read": True, "write": True})

    def test_get_participant_read_permissions(self):
        response = self.client.get(
            reverse(
                "api:gallery:detail-participant",
                kwargs={"pk_gallery": self.gallery_shared.pk, "user__pk": self.profile.user.pk},
            )
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data.get("id"), self.profile.user.pk)
        self.assertEqual(response.data.get("permissions"), {"read": True, "write": False})

    def test_get_participant_fail_permissions(self):
        response = self.client.get(
            reverse(
                "api:gallery:detail-participant",
                kwargs={"pk_gallery": self.gallery_other.pk, "user__pk": self.other.user.pk},
            )
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_put_modify_participant(self):
        user_gallery = UserGalleryFactory(user=self.new_participant.user, gallery=self.gallery, mode=GALLERY_READ)

        response = self.client.put(
            reverse(
                "api:gallery:detail-participant",
                kwargs={"pk_gallery": self.gallery.pk, "user__pk": self.new_participant.user.pk},
            ),
            {"can_write": True},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user_gallery = UserGallery.objects.get(pk=user_gallery.pk)
        self.assertEqual(user_gallery.mode, GALLERY_WRITE)

    def test_put_fail_modify_participant_not_participant(self):
        response = self.client.put(
            reverse(
                "api:gallery:detail-participant",
                kwargs={"pk_gallery": self.gallery.pk, "user__pk": self.new_participant.user.pk},
            ),
            {"can_write": True},
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_put_fail_modify_participant_linked_content(self):
        response = self.client.put(
            reverse(
                "api:gallery:detail-participant",
                kwargs={"pk_gallery": self.gallery_tuto.pk, "user__pk": self.new_participant.user.pk},
            ),
            {"can_write": False},
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        user_gallery = UserGallery.objects.get(gallery=self.gallery_tuto, user=self.new_participant.user)
        self.assertEqual(user_gallery.mode, GALLERY_WRITE)

    def test_put_fail_modify_participant_no_permissions(self):
        user_gallery = UserGalleryFactory(user=self.new_participant.user, gallery=self.gallery_other, mode=GALLERY_READ)

        response = self.client.put(
            reverse(
                "api:gallery:detail-participant",
                kwargs={"pk_gallery": self.gallery_other.pk, "user__pk": self.new_participant.user.pk},
            ),
            {"can_write": True},
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        user_gallery = UserGallery.objects.get(pk=user_gallery.pk)
        self.assertEqual(user_gallery.mode, GALLERY_READ)

    def test_put_fail_modify_participant_read_permissions(self):
        user_gallery = UserGalleryFactory(
            user=self.new_participant.user, gallery=self.gallery_shared, mode=GALLERY_READ
        )

        response = self.client.put(
            reverse(
                "api:gallery:detail-participant",
                kwargs={"pk_gallery": self.gallery_shared.pk, "user__pk": self.new_participant.user.pk},
            ),
            {"can_write": True},
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        user_gallery = UserGallery.objects.get(pk=user_gallery.pk)
        self.assertEqual(user_gallery.mode, GALLERY_READ)

    def test_delete_participant(self):
        UserGalleryFactory(user=self.new_participant.user, gallery=self.gallery)

        response = self.client.delete(
            reverse(
                "api:gallery:detail-participant",
                kwargs={"pk_gallery": self.gallery.pk, "user__pk": self.new_participant.user.pk},
            )
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(UserGallery.objects.filter(gallery=self.gallery, user=self.new_participant.user).count(), 0)

    def test_delete_participant_fail_linked_content(self):
        response = self.client.delete(
            reverse(
                "api:gallery:detail-participant",
                kwargs={"pk_gallery": self.gallery_tuto.pk, "user__pk": self.new_participant.user.pk},
            )
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        user_gallery = UserGallery.objects.get(gallery=self.gallery_tuto, user=self.new_participant.user)
        self.assertEqual(user_gallery.mode, GALLERY_WRITE)

    def test_delete_participant_fail_no_permissions(self):
        UserGalleryFactory(user=self.new_participant.user, gallery=self.gallery_other)

        response = self.client.delete(
            reverse(
                "api:gallery:detail-participant",
                kwargs={"pk_gallery": self.gallery_other.pk, "user__pk": self.new_participant.user.pk},
            )
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            UserGallery.objects.filter(gallery=self.gallery_other, user=self.new_participant.user).count(), 1
        )

    def test_delete_participant_fail_read_permissions(self):
        UserGalleryFactory(user=self.new_participant.user, gallery=self.gallery_shared)

        response = self.client.delete(
            reverse(
                "api:gallery:detail-participant",
                kwargs={"pk_gallery": self.gallery_shared.pk, "user__pk": self.new_participant.user.pk},
            )
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            UserGallery.objects.filter(gallery=self.gallery_shared, user=self.new_participant.user).count(), 1
        )
