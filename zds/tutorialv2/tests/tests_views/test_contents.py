import os

from django.conf import settings
from django.urls import reverse
from django.test import TestCase

from zds.gallery.models import Gallery, Image
from zds.gallery.factories import UserGalleryFactory
from zds.member.factories import ProfileFactory, StaffProfileFactory, UserFactory
from zds.tutorialv2.factories import (
    PublishableContentFactory,
    ContainerFactory,
    ExtractFactory,
    LicenceFactory,
    SubCategoryFactory,
)
from zds.tutorialv2.models.database import PublishableContent
from zds.tutorialv2.tests import TutorialTestMixin, override_for_contents
from zds.utils.models import Licence, SubCategory


# Needed to create the bot (for PM sending)
from django.contrib.auth.models import Group


@override_for_contents()
class DisplayContentTests(TutorialTestMixin, TestCase):
    # Front tests to write : check content is correct and properly formatted.
    # Some to potentially check : introduction, authors, conclusion, title, description, children title

    def create_users(self):
        self.user_staff = StaffProfileFactory().user
        self.user_author = ProfileFactory().user
        self.user_guest = ProfileFactory().user
        self.user_read_only_author = ProfileFactory(can_write=False).user

    def create_contents_set(self):
        self.contents = {}
        for _type in self.content_types:
            content = PublishableContentFactory(
                type=_type, introduction=f"{_type} introduction.", conclusion=f"{_type} conclusion."
            )
            content.authors.add(self.user_author)
            content.authors.add(self.user_read_only_author)
            content.save()
            self.contents[_type] = content

    def create_kwargs_to_display_contents(self):
        self.kwargs_to_display_contents = {}
        for content in self.contents.values():
            kwargs = {"pk": content.pk, "slug": content.slug}
            self.kwargs_to_display_contents[content] = kwargs

    def setUp(self):
        self.content_view_name = "content:view"
        self.content_types = ["TUTORIAL", "ARTICLE", "OPINION"]
        self.create_users()
        self.create_contents_set()
        self.create_kwargs_to_display_contents()

    def content_view_get(self, kwargs):
        return self.client.get(reverse(self.content_view_name, kwargs=kwargs))

    def redirect_login_url(self, content_kwargs):
        return reverse("member-login") + "?next=" + reverse(self.content_view_name, kwargs=content_kwargs)

    def test_public_cant_access_content_display_page(self):
        for content in self.contents.values():
            result = self.content_view_get(self.kwargs_to_display_contents[content])
            self.assertRedirects(
                result,
                self.redirect_login_url(self.kwargs_to_display_contents[content]),
                msg_prefix=f"Public should be redirected to login page if it tries to display {content.type} content.",
            )

    def test_guest_cant_access_content_display_page(self):
        self.login(self.user_guest, "hostel77")
        for content in self.contents.values():
            result = self.content_view_get(self.kwargs_to_display_contents[content])
            self.assertEqual(
                result.status_code,
                403,
                f"Guest user should obtain an error if he tries to display {content.type} content.",
            )
        self.logout()

    def test_read_only_author_can_access_content_display_page(self):
        self.login(self.user_read_only_author, "hostel77")
        for content in self.contents.values():
            result = self.content_view_get(self.kwargs_to_display_contents[content])
            self.assertEqual(
                result.status_code, 200, f"Read-only author should be able to display his {content.type} content."
            )
        self.logout()

    def test_author_can_access_content_display_page(self):
        self.login(self.user_author, "hostel77")
        a = True
        for content in self.contents.values():
            result = self.content_view_get(self.kwargs_to_display_contents[content])
            self.assertEqual(result.status_code, 200, f"Author should be able to display his {content.type} content.")
        self.logout()

    def test_staff_can_access_content_display_page(self):
        self.login(self.user_staff, "hostel77")
        for content in self.contents.values():
            result = self.content_view_get(self.kwargs_to_display_contents[content])
            self.assertEqual(
                result.status_code,
                200,
                f"Staff should be able to display {content.type} content even if he is not author.",
            )
        self.logout()


@override_for_contents()
class CreateContentAccessTests(TutorialTestMixin, TestCase):
    def create_users(self):
        self.user = ProfileFactory().user
        self.user_read_only = ProfileFactory(can_write=False).user

    def setUp(self):
        self.content_types = ["TUTORIAL", "ARTICLE", "OPINION"]
        self.create_users()

    def content_view_name(self, _type):
        return f"content:create-{_type.lower()}"

    def redirect_login_url(self, _type):
        return reverse("member-login") + "?next=" + reverse(self.content_view_name(_type))

    def test_public_cant_access_content_creation_page(self):
        for _type in self.content_types:
            result = self.content_create_get(_type)
            self.assertRedirects(
                result,
                self.redirect_login_url(_type),
                msg_prefix=f"Public should be redirected to login page if it tries access {_type} creation page.",
            )

    def test_read_only_user_cant_access_content_creation_page(self):
        self.login(self.user_read_only, "hostel77")
        for _type in self.content_types:
            result = self.content_create_get(_type.lower())
            self.assertEqual(
                result.status_code, 403, f"Read-only user should not be able to access {_type} creation page."
            )
        self.logout()

    def test_user_can_access_content_creation_page(self):
        self.login(self.user, "hostel77")
        for _type in self.content_types:
            result = self.content_create_get(_type.lower())
            self.assertEqual(result.status_code, 200, f"User should be able to access {_type} creation page.")
        self.logout()


@override_for_contents()
class CreateContentTests(TutorialTestMixin, TestCase):
    # Front tests to write : check it leads to content:view ie. content is correct and properly formatted.
    #                        check preview.
    #     # Refactor with preview_content_creation
    #     def test_preview_in_content_creation(self):
    #         self.login(self.user_author.username, 'hostel77')
    #         random_with_md = 'un text contenant du **markdown** .'
    #         response = self.client.post(
    #             reverse('content:create-tutorial'),
    #             {
    #                 'text': random_with_md,
    #                 'preview': '',
    #             }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

    #         self.assertEqual(response.status_code, 200)

    #         result_string = ''.join(str(a, 'utf-8') for a in response.streaming_content)
    #         self.assertIn('<strong>markdown</strong>', result_string, 'We need the text to be properly formatted')
    #         self.logout()

    def create_users(self):
        self.user = ProfileFactory().user
        self.user_read_only = ProfileFactory(can_write=False).user

    def create_kwargs_to_create_contents(self):
        self.kwargs_to_create_contents = {}
        for _type in self.content_types:
            kwargs = {
                "title": f"{_type} title",
                "description": f"{_type} description",
                "introduction": f"{_type} introduction",
                "conclusion": f"{_type} conclusion",
                "type": _type,
                "subcategory": self.subcategory.pk,
            }
            self.kwargs_to_create_contents[_type] = kwargs

    def setUp(self):
        self.content_types = ["TUTORIAL", "ARTICLE", "OPINION"]
        self.create_users()
        self.subcategory = SubCategoryFactory()
        self.create_kwargs_to_create_contents()

    def content_view_name(self, _type):
        return f"content:create-{_type.lower()}"

    def redirect_login_url(self, content_informations):
        _type = content_informations["type"].lower()
        return reverse("member-login") + "?next=" + reverse(self.content_view_name(_type))

    def test_public_cant_create_content(self):
        for _type in self.content_types:
            old_content_number = PublishableContent.objects.all().count()
            kwargs = self.kwargs_to_create_contents[_type]
            result = self.content_create_post(kwargs)
            self.assertRedirects(
                result,
                self.redirect_login_url(kwargs),
                msg_prefix=f"Public should be redirected to login page if it tries to create {_type}.",
            )
            current_content_number = PublishableContent.objects.all().count()
            self.assertEqual(
                current_content_number, old_content_number, "Its attempt should not add content to the database."
            )

    def test_read_only_cant_create_content(self):
        self.login(self.user_read_only, "hostel77")
        for _type in self.content_types:
            old_content_number = PublishableContent.objects.all().count()
            kwargs = self.kwargs_to_create_contents[_type]
            result = self.content_create_post(kwargs)
            self.assertEqual(
                result.status_code, 403, f"Read-only user should get an error if it tries to create {_type}."
            )
            current_content_number = PublishableContent.objects.all().count()
            self.assertEqual(
                current_content_number, old_content_number, "Its attempt should not add content to the database."
            )
        self.logout()

    def test_user_can_create_content(self):
        self.login(self.user, "hostel77")
        for _type in self.content_types:
            old_content_number = PublishableContent.objects.filter(type=_type).count()
            kwargs = self.kwargs_to_create_contents[_type]
            result = self.content_create_post(kwargs)
            self.assertEqual(
                result.status_code,
                302,
                f"User should be redirected to the page of the content created when he creates {_type}.",
            )
            current_content_number = PublishableContent.objects.filter(type=_type).count()
            self.assertEqual(
                current_content_number, old_content_number + 1, f"Its attempt should add a new {_type} to the database."
            )
            content = PublishableContent.objects.last()
            content_informations = kwargs.copy()
            content_informations["authors"] = set([self.user])
            content_informations["subcategory"] = set([kwargs["subcategory"]])
            self.check_content_informations(content, content_informations)
            self.check_content_gallery(content, set([self.user]))
        self.logout()

    def test_user_can_create_content_with_image(self):
        self.login(self.user, "hostel77")
        for _type in self.content_types:
            old_content_number = PublishableContent.objects.filter(type=_type).count()
            kwargs = self.kwargs_to_create_contents[_type]
            kwargs["image"] = open("{}/fixtures/noir_black.png".format(settings.BASE_DIR), "rb")
            result = self.content_create_post(kwargs)
            self.assertEqual(
                result.status_code,
                302,
                f"User should be redirected to the page of the content created when he creates {_type} with image.",
            )
            current_content_number = PublishableContent.objects.filter(type=_type).count()
            self.assertEqual(
                current_content_number, old_content_number + 1, f"Its attempt should add a new {_type} to the database."
            )
            content = PublishableContent.objects.last()
            content_informations = kwargs.copy()
            content_informations["authors"] = set([self.user])
            content_informations["subcategory"] = set([kwargs["subcategory"]])
            self.check_content_informations(content, content_informations)
            self.check_content_gallery(content, set([self.user]), size=1)
        self.logout()


@override_for_contents()
class EditContentAccessTests(TutorialTestMixin, TestCase):
    def create_users(self):
        self.user_staff = StaffProfileFactory().user
        self.user_author = ProfileFactory().user
        self.user_guest = ProfileFactory().user
        self.user_read_only_author = ProfileFactory(can_write=False).user

    def create_contents_set(self):
        self.contents = {}
        for _type in self.content_types:
            content = PublishableContentFactory(type=_type)
            content.authors.add(self.user_author)
            content.authors.add(self.user_read_only_author)
            content.save()
            self.contents[_type] = content

    def create_kwargs_to_edit_contents(self):
        self.kwargs_to_edit_contents = {}
        for content in self.contents.values():
            kwargs = {"pk": content.pk, "slug": content.slug}
            self.kwargs_to_edit_contents[content] = kwargs

    def setUp(self):
        self.content_types = ["TUTORIAL", "ARTICLE", "OPINION"]
        self.create_users()
        self.create_contents_set()
        self.create_kwargs_to_edit_contents()

    def test_public_cant_access_content_edition_page(self):
        for content in self.contents.values():
            result = self.content_edit_get(self.kwargs_to_edit_contents[content])
            self.assertEqual(
                result.status_code,
                302,
                f"Public should be redirected to login page if it tries to access {content.type} content edition page.",
            )

    def test_guest_cant_access_content_edition_page(self):
        self.login(self.user_guest, "hostel77")
        for content in self.contents.values():
            result = self.content_edit_get(self.kwargs_to_edit_contents[content])
            self.assertEqual(
                result.status_code,
                403,
                f"Guest user should obtain an error if he tries to access {content.type} content edition page.",
            )
        self.logout()

    def test_read_only_author_cant_access_content_edition_page(self):
        self.login(self.user_read_only_author, "hostel77")
        for content in self.contents.values():
            result = self.content_edit_get(self.kwargs_to_edit_contents[content])
            self.assertEqual(
                result.status_code,
                403,
                f"Read-only user should obtain an error if he tries to access {content.type} content edition page even if he is author.",
            )
        self.logout()

    def test_author_can_access_content_edition_page(self):
        self.login(self.user_author, "hostel77")
        for content in self.contents.values():
            result = self.content_edit_get(self.kwargs_to_edit_contents[content])
            self.assertEqual(
                result.status_code,
                200,
                f"Author should be able to access {content.type} content edition page of its content.",
            )
        self.logout()

    def test_staff_can_access_content_edition_page(self):
        self.login(self.user_staff, "hostel77")
        for content in self.contents.values():
            result = self.content_edit_get(self.kwargs_to_edit_contents[content])
            self.assertEqual(
                result.status_code,
                200,
                f"Staff should be able to access {content.type} content edition page even if he is not author.",
            )
        self.logout()


@override_for_contents()
class EditContentTests(TutorialTestMixin, TestCase):
    def create_users(self):
        self.user_staff = StaffProfileFactory().user
        self.user_author = ProfileFactory().user
        self.user_guest = ProfileFactory().user
        self.user_read_only_author = ProfileFactory(can_write=False).user

    def create_contents_set(self):
        self.contents = {}
        self.contents_old_informations = {}
        for _type in self.content_types:
            content = PublishableContentFactory(
                type=_type, introduction=f"{_type} introduction.", conclusion=f"{_type} conclusion."
            )
            content.authors.add(self.user_author)
            content.authors.add(self.user_read_only_author)
            UserGalleryFactory(gallery=content.gallery, user=self.user_author, mode="W")
            UserGalleryFactory(gallery=content.gallery, user=self.user_read_only_author, mode="W")
            content.save()
            self.contents[_type] = content
            self.contents_old_informations[content] = self.get_content_informations(content)

    def create_kwargs_to_edit_contents(self):
        self.kwargs_to_edit_contents = {}
        for content in self.contents.values():
            kwargs = {
                "description": f"{content.type} new description",
                "introduction": f"{content.type} new intro",
                "conclusion": f"{content.type} new conclusion",
                "type": content.type,
                "subcategory": self.new_subcategory.pk,
                "last_hash": content.load_version().compute_hash(),
            }
            self.kwargs_to_edit_contents[content] = kwargs

    def setUp(self):
        self.content_types = ["TUTORIAL", "ARTICLE", "OPINION"]
        self.create_users()
        self.new_subcategory = SubCategoryFactory()
        self.create_contents_set()
        self.create_kwargs_to_edit_contents()

    def test_public_cant_edit_content(self):
        for content in self.contents.values():
            kwargs = {"pk": content.pk, "slug": content.slug}
            content_informations = self.kwargs_to_edit_contents[content]
            content_informations["title"] = content.title
            result = self.content_edit_post(kwargs, content_informations)
            self.assertEqual(
                result.status_code,
                302,
                f"Public should be redirected to login page if it tries to edit {content.type} content.",
            )
            # Reload content
            content = PublishableContent.objects.get(pk=content.pk)
            self.check_content_informations(content, self.contents_old_informations[content])

    def test_guest_cant_edit_content(self):
        self.login(self.user_guest, "hostel77")
        for content in self.contents.values():
            kwargs = {"pk": content.pk, "slug": content.slug}
            content_informations = self.kwargs_to_edit_contents[content]
            content_informations["title"] = content.title
            result = self.content_edit_post(kwargs, content_informations)
            self.assertEqual(
                result.status_code,
                403,
                f"Guest user should obtain an error if he tries to edit {content.type} content.",
            )
            # Reload content
            content = PublishableContent.objects.get(pk=content.pk)
            self.check_content_informations(content, self.contents_old_informations[content])
        self.logout()

    def test_read_only_author_cant_edit_content(self):
        self.login(self.user_read_only_author, "hostel77")
        for content in self.contents.values():
            kwargs = {"pk": content.pk, "slug": content.slug}
            content_informations = self.kwargs_to_edit_contents[content]
            content_informations["title"] = content.title
            result = self.content_edit_post(kwargs, content_informations)
            self.assertEqual(
                result.status_code,
                403,
                f"Read-only user should obtain an error if he tries to edit {content.type} content even if he is author.",
            )
            # Reload content
            content = PublishableContent.objects.get(pk=content.pk)
            self.check_content_informations(content, self.contents_old_informations[content])
        self.logout()

    def test_author_can_edit_content(self):
        self.login(self.user_author, "hostel77")
        for content in self.contents.values():
            kwargs = {"pk": content.pk, "slug": content.slug}
            content_informations = self.kwargs_to_edit_contents[content]
            content_informations["title"] = content.title
            result = self.content_edit_post(kwargs, content_informations)
            self.assertEqual(result.status_code, 302, f"Author should be able to edit his {content.type} content.")

            content_informations["authors"] = set([self.user_author, self.user_read_only_author])
            content_informations["subcategory"] = set([content_informations["subcategory"]])
            # Reload content
            content = PublishableContent.objects.get(pk=content.pk)
            self.check_content_informations(content, content_informations)
        self.logout()

    def test_staff_can_edit_content(self):
        self.login(self.user_staff, "hostel77")
        for content in self.contents.values():
            kwargs = {"pk": content.pk, "slug": content.slug}
            content_informations = self.kwargs_to_edit_contents[content]
            content_informations["title"] = content.title
            result = self.content_edit_post(kwargs, content_informations)
            self.assertEqual(
                result.status_code,
                302,
                f"Staff should be able to edit {content.type} content even if he is not author.",
            )
            content_informations["authors"] = set([self.user_author, self.user_read_only_author])
            content_informations["subcategory"] = set([content_informations["subcategory"]])
            # Reload content
            content = PublishableContent.objects.get(pk=content.pk)
            self.check_content_informations(content, content_informations)
        self.logout()

    def test_edition_with_new_title(self):
        self.login(self.user_author, "hostel77")
        for content in self.contents.values():
            kwargs = {"pk": content.pk, "slug": content.slug}
            content_informations = self.kwargs_to_edit_contents[content]
            content_informations["title"] = "new_title"
            result = self.content_edit_post(kwargs, content_informations)
            self.assertEqual(
                result.status_code, 302, f"Author should be able to edit his {content.type} content and edit the title."
            )
            # Reload content
            new_version = PublishableContent.objects.get(pk=content.pk)
            content_informations["authors"] = set([self.user_author, self.user_read_only_author])
            content_informations["subcategory"] = set([content_informations["subcategory"]])
            self.check_content_informations(new_version, content_informations)
            self.assertNotEqual(
                new_version.slug,
                content.slug,
                f"The #{content.type} content slug should have changed since its title has been modified.",
            )
            self.assertEqual(
                self.content_view_get({"pk": content.pk, "slug": content.slug}).status_code,
                404,
                f"Author should not be able to access its {content.type} content using old slug.",
            )
            self.assertEqual(
                self.content_view_get({"pk": content.pk, "slug": new_version.slug}).status_code,
                200,
                f"Author should be able to access its {content.type} content using the new slug.",
            )
        self.logout()

    def test_edition_with_new_icon(self):
        self.login(self.user_author, "hostel77")
        for content in self.contents.values():
            kwargs = {"pk": content.pk, "slug": content.slug}
            content_informations = self.kwargs_to_edit_contents[content]
            content_informations["title"] = content.title
            content_informations["image"] = open("{}/fixtures/noir_black.png".format(settings.BASE_DIR), "rb")
            images_number = Image.objects.filter(gallery__pk=content.gallery.pk).count()
            result = self.content_edit_post(kwargs, content_informations)
            self.assertEqual(
                result.status_code,
                302,
                f"Author should be able to edit his {content.type} content and change its icon.",
            )
            content_informations["authors"] = set([self.user_author, self.user_read_only_author])
            content_informations["subcategory"] = set([content_informations["subcategory"]])
            # Reload content
            old_content = content
            content = PublishableContent.objects.get(pk=content.pk)
            self.check_content_informations(content, content_informations)
            self.check_content_gallery(content, set(content.authors.all()), images_number + 1)
        self.logout()

    def test_edition_without_hash_fails(self):
        self.login(self.user_author, "hostel77")
        for content in self.contents.values():
            kwargs = {"pk": content.pk, "slug": content.slug}
            content_informations = self.kwargs_to_edit_contents[content]
            content_informations["title"] = content.title
            content_informations["last_hash"] = ""
            result = self.content_edit_post(kwargs, content_informations)
            self.assertEqual(result.status_code, 200, f"Edition should fails if it does not provides a correct hash.")
            # Reload content
            content = PublishableContent.objects.get(pk=content.pk)
            self.check_content_informations(content, self.contents_old_informations[content])
        self.logout()


@override_for_contents()
class DeleteContentTests(TutorialTestMixin, TestCase):
    def create_users(self):
        self.user_author = ProfileFactory().user
        self.user_read_only_author = ProfileFactory(can_write=False).user
        self.user_guest = ProfileFactory().user
        self.user_staff = StaffProfileFactory().user

    def create_contents_set(self):
        self.contents = {}
        for _type in self.content_types:
            content = PublishableContentFactory(type=_type)
            content.save()
            self.contents[_type] = content

    def create_kwargs_to_delete_contents(self):
        self.kwargs_to_delete_contents = {}
        for content in self.contents.values():
            kwargs = {"pk": content.pk, "slug": content.slug}
            self.kwargs_to_delete_contents[content] = kwargs

    def setUp(self):
        self.content_types = ["TUTORIAL", "ARTICLE", "OPINION"]
        self.create_users()
        self.create_contents_set()
        self.create_kwargs_to_delete_contents()

    def test_public_cant_delete_content(self):
        for content in self.contents.values():
            result = self.content_delete_post(self.kwargs_to_delete_contents[content])
            self.assertEqual(
                result.status_code,
                302,
                f"Public should be redirected to login page if it tries to delete {content.type} content.",
            )
            self.assertEqual(
                PublishableContent.objects.filter(pk=content.pk).count(), 1, f"Content should not have been deleted."
            )

    def test_guest_cant_delete_content(self):
        self.login(self.user_guest, "hostel77")
        for content in self.contents.values():
            result = self.content_delete_post(self.kwargs_to_delete_contents[content])
            self.assertEqual(
                result.status_code,
                403,
                f"Guest user should obtain an error if he tries to delete {content.type} content.",
            )
            self.assertEqual(
                PublishableContent.objects.filter(pk=content.pk).count(), 1, f"Content should not have been deleted."
            )
        self.logout()

    def test_read_only_author_can_delete_content(self):
        self.login(self.user_read_only_author, "hostel77")
        for content in self.contents.values():
            content.authors.add(self.user_read_only_author)
            UserGalleryFactory(gallery=content.gallery, user=self.user_read_only_author, mode="W")
            content.save()
            versioned = content.load_version()
            gallery = content.gallery
            result = self.content_delete_post(self.kwargs_to_delete_contents[content])
            self.assertEqual(
                result.status_code,
                302,
                f"Read-only author should be able to delete a {content.type} content if he is author.",
            )
            self.assertEqual(
                PublishableContent.objects.filter(pk=content.pk).count(), 0, f"Content should have been deleted."
            )
            self.assertFalse(os.path.isfile(versioned.get_path()), "MESSAGE TO WRITE")
            self.assertEqual(
                Gallery.objects.filter(pk=gallery.pk).count(), 0, f"{content.type} gallery should have been deleted."
            )
        self.logout()

    def test_staff_cant_delete_content(self):
        self.login(self.user_staff, "hostel77")
        for content in self.contents.values():
            result = self.content_delete_post(self.kwargs_to_delete_contents[content])
            self.assertEqual(
                result.status_code,
                403,
                f"Staff should not be able to delete {content.type} content if he is not author.",
            )
            self.assertEqual(
                PublishableContent.objects.filter(pk=content.pk).count(), 1, f"Content should not have been deleted."
            )
        self.logout()

    def test_author_can_delete_content(self):
        self.login(self.user_author, "hostel77")
        for content in self.contents.values():
            content.authors.add(self.user_author)
            UserGalleryFactory(gallery=content.gallery, user=self.user_author, mode="W")
            content.save()
            versioned = content.load_version()
            gallery = content.gallery
            result = self.content_delete_post(self.kwargs_to_delete_contents[content])
            self.assertEqual(result.status_code, 302, f"Author should be able to delete his {content.type} content.")
            self.assertEqual(
                PublishableContent.objects.filter(pk=content.pk).count(),
                0,
                f"{content.type} content should have been deleted.",
            )
            self.assertFalse(os.path.isfile(versioned.get_path()), "MESSAGE TO WRITE")
            self.assertEqual(
                Gallery.objects.filter(pk=gallery.pk).count(), 0, f"{content.type} gallery should have been deleted."
            )
        self.logout()

    def test_deletion_when_other_authors_just_remove_author_from_list(self):
        self.login(self.user_guest, "hostel77")
        for content in self.contents.values():
            content.authors.add(self.user_author)
            content.authors.add(self.user_guest)
            UserGalleryFactory(gallery=content.gallery, user=self.user_author, mode="W")
            UserGalleryFactory(gallery=content.gallery, user=self.user_guest, mode="W")
            content.save()
            result = self.content_delete_post(self.kwargs_to_delete_contents[content])
            self.assertEqual(
                result.status_code,
                302,
                f"MESSAGE TO CHANGE : Author should be able to delete his {content.type} content.",
            )
            self.assertEqual(
                PublishableContent.objects.filter(pk=content.pk).count(),
                1,
                f"Content should not have been deleted since there were multiple authors.",
            )
            old_content = content
            content = PublishableContent.objects.get(pk=content.pk)
            self.assertEqual(content.authors.count(), 1)
            self.assertIn(self.user_author, content.authors.all())
            # Only user_author should be able to access the content gallery since user_guest is no more author.
            self.check_content_gallery(old_content, set(old_content.authors.all()))
        self.logout()

    def test_cant_delete_with_get(self):
        self.login(self.user_author, "hostel77")
        for content in self.contents.values():
            content.authors.add(self.user_author)
            content.save()
            result = self.client.get(
                reverse("content:delete", kwargs=self.kwargs_to_delete_contents[content]), follow=False
            )
            self.assertEqual(
                result.status_code,
                405,
                f"Author should not be able to delete his {content.type} content using GET request.",
            )
            self.assertEqual(
                PublishableContent.objects.filter(pk=content.pk).count(), 1, f"Content should not have been deleted."
            )
        self.logout()


@override_for_contents()
class DownloadContentTests(TutorialTestMixin, TestCase):
    def create_users(self):
        self.user_staff = StaffProfileFactory().user
        self.user_author = ProfileFactory().user
        self.user_guest = ProfileFactory().user
        self.user_read_only_author = ProfileFactory(can_write=False).user

    def create_contents_set(self):
        self.contents = {}
        for _type in self.content_types:
            content = PublishableContentFactory(type=_type)
            content.authors.add(self.user_author)
            content.authors.add(self.user_read_only_author)
            content.save()
            self.contents[_type] = content

    def create_kwargs_to_download_contents(self):
        self.kwargs_to_download_contents = {}
        for content in self.contents.values():
            kwargs = {"pk": content.pk, "slug": content.slug}
            self.kwargs_to_download_contents[content] = kwargs

    def setUp(self):
        self.content_types = ["TUTORIAL", "ARTICLE", "OPINION"]
        self.create_users()
        self.create_contents_set()
        self.create_kwargs_to_download_contents()

    def test_public_cant_download_content(self):
        for content in self.contents.values():
            result = self.content_download_get(self.kwargs_to_download_contents[content])
            self.assertEqual(
                result.status_code,
                302,
                f"Public should be redirected to login page if it tries to download {content.type}.",
            )

    def test_guest_cant_download_content(self):
        self.login(self.user_guest, "hostel77")
        for content in self.contents.values():
            result = self.content_edit_get(self.kwargs_to_download_contents[content])
            self.assertEqual(
                result.status_code,
                403,
                f"Guest user should obtain an error if he tries to download {content.type} content.",
            )
        self.logout()

    def test_read_only_author_cant_download_content(self):
        self.login(self.user_read_only_author, "hostel77")
        for content in self.contents.values():
            result = self.content_edit_get(self.kwargs_to_download_contents[content])
            self.assertEqual(
                result.status_code,
                403,
                f"Read-only user should obtain an error if he tries to download {content.type} content even if he is author.",
            )
        self.logout()

    def test_author_can_download_content(self):
        self.login(self.user_author, "hostel77")
        for content in self.contents.values():
            result = self.content_edit_get(self.kwargs_to_download_contents[content])
            self.assertEqual(result.status_code, 200, f"Author should be able to download its {content.type} content.")
        self.logout()

    def test_staff_can_download_content(self):
        self.login(self.user_staff, "hostel77")
        for content in self.contents.values():
            result = self.content_edit_get(self.kwargs_to_download_contents[content])
            self.assertEqual(
                result.status_code,
                200,
                f"Staff should be able to download {content.type} content even if he is not author.",
            )
        self.logout()


@override_for_contents()
class AddAuthorToContentTests(TutorialTestMixin, TestCase):
    def create_users(self):
        self.user_author = ProfileFactory().user
        self.user_read_only_author = ProfileFactory(can_write=False).user
        self.user_guest = ProfileFactory().user
        self.new_author = ProfileFactory().user
        self.user_staff = StaffProfileFactory().user

    def create_contents_set(self):
        self.contents = {}
        for _type in self.content_types:
            content = PublishableContentFactory(type=_type)
            content.authors.add(self.user_author)
            content.authors.add(self.user_read_only_author)
            content.save()
            self.contents[_type] = content
            if _type == "TUTORIAL":
                self.pk = content.pk

    def create_kwargs_to_add_author_to_contents(self):
        self.kwargs_to_add_author = {}
        for content in self.contents.values():
            kwargs = {"pk": content.pk}
            self.kwargs_to_add_author[content] = kwargs

    def setUp(self):
        self.content_types = ["TUTORIAL", "ARTICLE", "OPINION"]
        self.create_users()
        self.create_contents_set()
        self.create_kwargs_to_add_author_to_contents()
        self.new_author_informations = {"username": self.new_author.username}
        self.bot_user = ProfileFactory().user
        self.overridden_zds_app["member"]["bot_account"] = self.bot_user.username
        bot = Group(name=self.overridden_zds_app["member"]["bot_group"])
        bot.save()

    def test_public_cant_add_author_to_content(self):
        for content in self.contents.values():
            kwargs_content = self.kwargs_to_add_author[content]
            result = self.content_add_author_post(kwargs_content, self.new_author_informations)
            self.assertEqual(
                result.status_code,
                302,
                f"Public should be redirected to login page if it tries to add author to {content.type} content.",
            )
            self.assertEqual(PublishableContent.objects.get(pk=content.pk).authors.count(), 2, f"It should a.")

    def test_guest_cant_add_author_to_content(self):
        self.login(self.user_guest, "hostel77")
        for content in self.contents.values():
            kwargs_content = self.kwargs_to_add_author[content]
            result = self.content_add_author_post(kwargs_content, self.new_author_informations)
            self.assertEqual(
                result.status_code,
                403,
                f"Guest user should obtain an error if he tries to add author to {content.type} content.",
            )
        self.logout()

    def test_read_only_author_cant_add_author_to_content(self):
        self.login(self.user_read_only_author, "hostel77")
        for content in self.contents.values():
            content.authors.add(self.user_read_only_author)
            content.save()
            kwargs_content = self.kwargs_to_add_author[content]
            result = self.content_add_author_post(kwargs_content, self.new_author_informations)
            self.assertEqual(
                result.status_code,
                403,
                f"Read-only author should obtain an error if he tries to add author to a {content.type} content even if he is author.",
            )
        self.logout()

    def test_staff_can_add_author_to_content(self):
        self.login(self.user_staff, "hostel77")
        for content in self.contents.values():
            kwargs_content = self.kwargs_to_add_author[content]
            result = self.content_add_author_post(kwargs_content, self.new_author_informations)
            self.assertEqual(
                result.status_code,
                302,
                f"Staff should be able to add author to {content.type} content even if he is not author.",
            )

            # Reload content
            content_authors = PublishableContent.objects.get(pk=content.pk).authors
            self.assertEqual(content_authors.count(), 3, f"The author number should have been incremented.")
            self.assertIn(self.new_author, content_authors.all())
        self.logout()

    def test_author_can_add_author_to_content(self):
        self.login(self.user_author, "hostel77")
        for content in self.contents.values():
            kwargs_content = self.kwargs_to_add_author[content]
            result = self.content_add_author_post(kwargs_content, self.new_author_informations)
            self.assertEqual(
                result.status_code, 302, f"Author should be able to add author to his {content.type} content."
            )
            content_authors = PublishableContent.objects.get(pk=content.pk).authors
            self.assertEqual(content_authors.count(), 3, f"The author number should have been incremented.")
            self.assertIn(self.new_author, content_authors.all())
        self.logout()

    def test_author_cant_add_unknown_user_to_content(self):
        self.login(self.user_author, "hostel77")
        for content in self.contents.values():
            kwargs_content = self.kwargs_to_add_author[content]
            result = self.content_add_author_post(kwargs_content, {"username": "unknown"})
            self.assertEqual(
                result.status_code, 302, f"Attempting to add an unexisting user should not lead to an error."
            )
            content_authors = PublishableContent.objects.get(pk=content.pk).authors
            self.assertEqual(
                content_authors.count(),
                2,
                f"Attempting to add an unexisting error should not change the number of author.",
            )
        self.logout()


@override_for_contents()
class DisplayContainerTests(TutorialTestMixin, TestCase):
    def create_users(self):
        self.user_staff = StaffProfileFactory().user
        self.user_author = ProfileFactory().user
        self.user_guest = ProfileFactory().user
        self.user_read_only_author = ProfileFactory(can_write=False).user

    def create_tutorial(self):
        self.tutorial = PublishableContentFactory(
            type="TUTORIAL", introduction="tutorial introduction", conclusion="tutorial conclusion"
        )
        self.tutorial.authors.add(self.user_author)
        self.tutorial.authors.add(self.user_read_only_author)
        self.tutorial.save()
        self.containers = []
        container = ContainerFactory(
            parent=self.tutorial.load_version(),
            db_object=self.tutorial,
            introduction="container 0 introduction",
            conclusion="container 0 conclusion",
        )
        self.containers.append(container)
        for i in range(1, self.max_depth_container):
            container = ContainerFactory(
                parent=container,
                db_object=self.tutorial,
                introduction=f"container {i} introduction",
                conclusion=f"container {i} conclusion",
            )
            self.containers.append(container)

    def setUp(self):
        self.container_slug_keys = ["container_slug", "parent_container_slug"]
        self.max_depth_container = settings.ZDS_APP["content"]["max_tree_depth"] - 1
        self.create_users()
        self.create_tutorial()

    def test_public_cant_access_container_display_page(self):
        for (depth, container) in enumerate(self.containers):
            kwargs = {"pk": self.tutorial.pk, "slug": self.tutorial.slug}
            for i in range(depth + 1):
                kwargs[self.container_slug_keys[depth - i]] = self.containers[i].slug
            result = self.container_view_get(kwargs)
            self.assertEqual(
                result.status_code, 302, f"Public should not be able to display level {depth} container in tutorial."
            )

    def test_guest_cant_access_container_display_page(self):
        self.login(self.user_guest, "hostel77")
        for (depth, container) in enumerate(self.containers):
            kwargs = {"pk": self.tutorial.pk, "slug": self.tutorial.slug}
            for i in range(depth + 1):
                kwargs[self.container_slug_keys[depth - i]] = self.containers[i].slug
            result = self.container_view_get(kwargs)
            self.assertEqual(
                result.status_code, 403, f"Guest should not be able to display level {depth} container in tutorial."
            )
        self.logout()

    def test_read_only_author_can_access_container_display_page(self):
        self.login(self.user_read_only_author, "hostel77")
        for (depth, container) in enumerate(self.containers):
            kwargs = {"pk": self.tutorial.pk, "slug": self.tutorial.slug}
            for i in range(depth + 1):
                kwargs[self.container_slug_keys[depth - i]] = self.containers[i].slug
            result = self.container_view_get(kwargs)
            self.assertEqual(
                result.status_code,
                200,
                f"Read-only author should be able to display level {depth} container in tutorial even if he is author.",
            )
        self.logout()

    def test_author_can_access_container_display_page(self):
        self.login(self.user_author, "hostel77")
        for (depth, container) in enumerate(self.containers):
            kwargs = {"pk": self.tutorial.pk, "slug": self.tutorial.slug}
            for i in range(depth + 1):
                kwargs[self.container_slug_keys[depth - i]] = self.containers[i].slug
            result = self.container_view_get(kwargs)
            self.assertEqual(
                result.status_code, 200, f"Author should be able to display level {depth} container in his tutorial."
            )
        self.logout()

    def test_staff_can_access_container_display_page(self):
        self.login(self.user_staff, "hostel77")
        for (depth, container) in enumerate(self.containers):
            kwargs = {"pk": self.tutorial.pk, "slug": self.tutorial.slug}
            for i in range(depth + 1):
                kwargs[self.container_slug_keys[depth - i]] = self.containers[i].slug
            result = self.container_view_get(kwargs)
            self.assertEqual(
                result.status_code, 200, f"Staff should be able to display level {depth} container in tutorial."
            )
        self.logout()


@override_for_contents()
class EditContainerAccessTests(TutorialTestMixin, TestCase):
    def create_users(self):
        self.user_staff = StaffProfileFactory().user
        self.user_author = ProfileFactory().user
        self.user_guest = ProfileFactory().user
        self.user_read_only_author = ProfileFactory(can_write=False).user

    def create_tutorial(self):
        self.tutorial = PublishableContentFactory(
            type="TUTORIAL", introduction="tutorial introduction", conclusion="tutorial conclusion"
        )
        self.tutorial.authors.add(self.user_author)
        self.tutorial.authors.add(self.user_read_only_author)
        self.tutorial.save()
        self.containers = []
        container = ContainerFactory(
            parent=self.tutorial.load_version(),
            db_object=self.tutorial,
            introduction="container 0 introduction",
            conclusion="container 0 conclusion",
        )
        self.containers.append(container)
        for i in range(1, self.max_depth_container):
            container = ContainerFactory(
                parent=container,
                db_object=self.tutorial,
                introduction=f"container {i} introduction",
                conclusion=f"container {i} conclusion",
            )
            self.containers.append(container)

    def setUp(self):
        self.container_slug_keys = ["container_slug", "parent_container_slug"]
        self.max_depth_container = settings.ZDS_APP["content"]["max_tree_depth"] - 1
        self.create_users()
        self.create_tutorial()

    def test_public_cant_access_container_edit_page(self):
        for (depth, container) in enumerate(self.containers):
            kwargs = {"pk": self.tutorial.pk, "slug": self.tutorial.slug}
            for i in range(depth + 1):
                kwargs[self.container_slug_keys[depth - i]] = self.containers[i].slug
            result = self.container_edit_get(kwargs)
            self.assertEqual(
                result.status_code, 302, f"Public should not be able to access level {depth} container edition page."
            )

    def test_guest_cant_access_container_edit_page(self):
        self.login(self.user_guest, "hostel77")
        for (depth, container) in enumerate(self.containers):
            kwargs = {"pk": self.tutorial.pk, "slug": self.tutorial.slug}
            for i in range(depth + 1):
                kwargs[self.container_slug_keys[depth - i]] = self.containers[i].slug
            result = self.container_edit_get(kwargs)
            self.assertEqual(
                result.status_code, 403, f"Guest should not be able to access level {depth} container edition page."
            )
        self.logout()

    def test_read_only_author_cant_access_container_edit_page(self):
        self.login(self.user_read_only_author, "hostel77")
        for (depth, container) in enumerate(self.containers):
            kwargs = {"pk": self.tutorial.pk, "slug": self.tutorial.slug}
            for i in range(depth + 1):
                kwargs[self.container_slug_keys[depth - i]] = self.containers[i].slug
            result = self.container_edit_get(kwargs)
            self.assertEqual(
                result.status_code,
                403,
                f"Read-only author should not be able to access level {depth} container edition page even if he is author.",
            )
        self.logout()

    def test_author_can_access_container_edit_page(self):
        self.login(self.user_author, "hostel77")
        for (depth, container) in enumerate(self.containers):
            kwargs = {"pk": self.tutorial.pk, "slug": self.tutorial.slug}
            for i in range(depth + 1):
                kwargs[self.container_slug_keys[depth - i]] = self.containers[i].slug
            result = self.container_edit_get(kwargs)
            self.assertEqual(
                result.status_code,
                200,
                f"Author should be able to access level {depth} container edition page of his tutorial.",
            )
        self.logout()

    def test_staff_can_access_container_edit_page(self):
        self.login(self.user_staff, "hostel77")
        for (depth, container) in enumerate(self.containers):
            kwargs = {"pk": self.tutorial.pk, "slug": self.tutorial.slug}
            for i in range(depth + 1):
                kwargs[self.container_slug_keys[depth - i]] = self.containers[i].slug
            result = self.container_edit_get(kwargs)
            self.assertEqual(
                result.status_code, 200, f"Staff should be able to access level {depth} container edition page."
            )
        self.logout()
