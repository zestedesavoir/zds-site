from django.conf import settings
from django.urls import reverse
from django.test import TestCase

from zds.gallery.factories import UserGalleryFactory
from zds.gallery.models import UserGallery, Gallery
from zds.gallery.models import Image
from zds.member.factories import ProfileFactory, StaffProfileFactory, UserFactory
from zds.tutorialv2.factories import PublishableContentFactory, ContainerFactory, ExtractFactory, LicenceFactory, SubCategoryFactory
from zds.tutorialv2.models.database import PublishableContent
from zds.tutorialv2.tests import TutorialTestMixin, override_for_contents


# Front tests to write : check content is correct and properly formatted.
# Some to potentially check : introduction, authors, conclusion, title, description, children title
@override_for_contents()
class DisplayContentTests(TutorialTestMixin, TestCase):

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

    def create_kwargs_to_display_contents(self):
        self.kwargs_to_display_contents = {}
        for content in self.contents.values():
            kwargs = {'pk': content.pk, 'slug': content.slug}
            self.kwargs_to_display_contents[content] = kwargs

    def setUp(self):
        self.content_types = ['TUTORIAL', 'ARTICLE', 'OPINION']
        self.create_users()
        self.create_contents_set()
        self.create_kwargs_to_display_contents()

    def test_public_cant_access_content_display_page(self):
        for content in self.contents.values():
            result = self.access_content_display_page(self.kwargs_to_display_contents[content])
            self.assertEqual(
                result.status_code,
                302,
                f'Public should be redirected to login page if it tries to display {content.type} content.'
            )

    def test_guest_cant_access_content_display_page(self):
        self.login(self.user_guest, 'hostel77')
        for content in self.contents.values():
            result = self.access_content_display_page(self.kwargs_to_display_contents[content])
            self.assertEqual(
                result.status_code,
                403,
                f'Guest user should obtain an error if he tries to display {content.type} content.'
            )
        self.logout()

    def test_read_only_author_can_access_content_display_page(self):
        self.login(self.user_read_only_author, 'hostel77')
        for content in self.contents.values():
            result = self.access_content_display_page(self.kwargs_to_display_contents[content])
            self.assertEqual(
                result.status_code,
                200,
                f'Read-only author should be able to display his {content.type} content.'
            )
        self.logout()


    def test_author_can_access_content_display_page(self):
        self.login(self.user_author, 'hostel77')
        for content in self.contents.values():
            result = self.access_content_display_page(self.kwargs_to_display_contents[content])
            self.assertEqual(
                result.status_code,
                200,
                f'Author should be able to display his {content.type} content.'
            )
        self.logout()

    def test_staff_can_access_content_display_page(self):
        self.login(self.user_staff, 'hostel77')
        for content in self.contents.values():
            result = self.access_content_display_page(self.kwargs_to_display_contents[content])
            self.assertEqual(
                result.status_code,
                200,
                f'Staff should be able to display {content.type} content even if he is not author.'
            )
        self.logout()

@override_for_contents()
class CreateContentAccessTests(TutorialTestMixin, TestCase):

    def create_users(self):
        self.user = ProfileFactory().user
        self.user_read_only = ProfileFactory(can_write=False).user

    def setUp(self):
        self.content_types = ['TUTORIAL', 'ARTICLE', 'OPINION']
        self.create_users()

    def test_public_cant_access_content_creation_page(self):
        for _type in self.content_types:
            result = self.access_content_creation_page(_type)
            self.assertEqual(
                result.status_code,
                302,
                f'Public should be redirected to login page if it tries access {_type} creation page.'
            )

    def test_read_only_user_cant_access_content_creation_page(self):
        self.login(self.user_read_only, 'hostel77')
        for _type in self.content_types:
            result = self.access_content_creation_page(_type.lower())
            self.assertEqual(
                result.status_code,
                403,
                f'Read-only user should not be able to access {_type} creation page.'
            )
        self.logout()

    def test_user_can_access_content_creation_page(self):
        self.login(self.user, 'hostel77')
        for _type in self.content_types:
            result = self.access_content_creation_page(_type.lower())
            self.assertEqual(
                result.status_code,
                200,
                f'User should be able to access {_type} creation page.'
            )
        self.logout()


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
@override_for_contents()
class CreateContentTests(TutorialTestMixin, TestCase):
    def create_users(self):
        self.user = ProfileFactory().user
        self.user_read_only = ProfileFactory(can_write=False).user

    def create_kwargs_to_create_contents(self):
        self.kwargs_to_create_contents = {}
        for _type in self.content_types:
            kwargs = {
                'title': 'un titre',
                'description': 'une description',
                'introduction': 'une intro',
                'conclusion': 'une conclusion',
                'type': _type,
                'licence': self.licence.pk,
                'subcategory': self.subcategory.pk
            }
            self.kwargs_to_create_contents[_type] = kwargs

    def setUp(self):
        self.content_types = ['TUTORIAL', 'ARTICLE', 'OPINION']
        self.create_users()
        self.licence = LicenceFactory()
        self.subcategory = SubCategoryFactory()
        self.create_kwargs_to_create_contents()

    def test_public_cant_create_content(self):
        for _type in self.content_types:
            old_content_number = PublishableContent.objects.all().count()
            kwargs = self.kwargs_to_create_contents[_type]
            result = self.create_content(kwargs)
            self.assertEqual(
                result.status_code,
                302,
                f'Public should be redirected to login page if it tries to create {_type}.'
            )
            current_content_number = PublishableContent.objects.all().count()
            self.assertEqual(
                current_content_number,
                old_content_number,
                'Its attempt should not add content to the database.'
            )

    def test_read_only_cant_create_content(self):
        self.login(self.user_read_only, 'hostel77')
        for _type in self.content_types:
            old_content_number = PublishableContent.objects.all().count()
            kwargs = self.kwargs_to_create_contents[_type]
            result = self.create_content(kwargs)
            self.assertEqual(
                result.status_code,
                403,
                f'Read-only user should get an error if it tries to create {_type}.'
            )
            current_content_number = PublishableContent.objects.all().count()
            self.assertEqual(
                current_content_number,
                old_content_number,
                'Its attempt should not add content to the database.'
            )
        self.logout()

    def test_user_can_create_content(self):
        self.login(self.user, 'hostel77')
        for _type in self.content_types:
            old_content_number = PublishableContent.objects.filter(type=_type).count()
            kwargs = self.kwargs_to_create_contents[_type]
            result = self.create_content(kwargs)
            self.assertEqual(
                result.status_code,
                302,
                f'User should be redirected to the page of the content created when he creates {_type}.'
            )
            current_content_number = PublishableContent.objects.filter(type=_type).count()
            self.assertEqual(
                current_content_number,
                old_content_number + 1,
                f'Its attempt should add a new {_type} to the database.'
            )

            content = PublishableContent.objects.last()
            self.assertIn(
                self.user,
                content.authors.all(),
                f'User should be author of the new {_type}.'
            )
            self.assertEqual(
                content.authors.count(),
                1,
                f'User should be the only author of the new {_type}.'
            )

        self.logout()

    def test_user_can_create_content_with_image(self):
        self.login(self.user, 'hostel77')
        for _type in self.content_types:
            old_content_number = PublishableContent.objects.filter(type=_type).count()
            kwargs = self.kwargs_to_create_contents[_type]
            kwargs['image'] = open('{}/fixtures/noir_black.png'.format(settings.BASE_DIR), 'rb')
            result = self.create_content(kwargs)
            self.assertEqual(
                result.status_code,
                302,
                f'User should be redirected to the page of the content created when he creates {_type} with image.'
            )
            current_content_number = PublishableContent.objects.filter(type=_type).count()
            self.assertEqual(
                current_content_number,
                old_content_number + 1,
                f'Its attempt should add a new {_type} to the database.'
            )

            content = PublishableContent.objects.last()
            self.assertIn(
                self.user,
                content.authors.all(),
                f'User should be author of the new {_type}.'
            )
            self.assertEqual(
                content.authors.count(),
                1,
                f'User should be the only author of the new {_type}.'
            )

            content = PublishableContent.objects.last()
            self.assertEqual(
                Gallery.objects.filter(pk=content.gallery.pk).count(),
                1,
                f'A gallery linked to the new {_type} should have been created.'
            )
            self.assertEqual(
                UserGallery.objects.filter(gallery__pk=content.gallery.pk).count(),
                1,
                f'User should have access the gallery of the new {_type}.'
            )
            self.assertEqual(
                Image.objects.filter(gallery__pk=content.gallery.pk).count(),
                1,
                f'Gallery of the new {_type} should contains one image.'
            )
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
            kwargs = {'pk': content.pk, 'slug': content.slug}
            self.kwargs_to_edit_contents[content] = kwargs

    def setUp(self):
        self.content_types = ['TUTORIAL', 'ARTICLE', 'OPINION']
        self.create_users()
        self.create_contents_set()
        self.create_kwargs_to_edit_contents()

    def test_public_cant_access_content_edition_page(self):
        for content in self.contents.values():
            result = self.access_content_edition_page(self.kwargs_to_edit_contents[content])
            self.assertEqual(
                result.status_code,
                302,
                f'Public should be redirected to login page if it tries to access {content.type} content edition page.'
            )

    def test_guest_cant_access_content_edition_page(self):
        self.login(self.user_guest, 'hostel77')
        for content in self.contents.values():
            result = self.access_content_edition_page(self.kwargs_to_edit_contents[content])
            self.assertEqual(
                result.status_code,
                403,
                f'Guest user should obtain an error if he tries to access {content.type} content edition page.'
            )
        self.logout()

    def test_read_only_author_cant_access_content_edition_page(self):
        self.login(self.user_read_only_author, 'hostel77')
        for content in self.contents.values():
            result = self.access_content_edition_page(self.kwargs_to_edit_contents[content])
            self.assertEqual(
                result.status_code,
                403,
                f'Read-only user should obtain an error if he tries to access {content.type} content edition page even if he is author.'
            )
        self.logout()

    def test_author_can_access_content_edition_page(self):
        self.login(self.user_author, 'hostel77')
        for content in self.contents.values():
            result = self.access_content_edition_page(self.kwargs_to_edit_contents[content])
            self.assertEqual(
                result.status_code,
                200,
                f'Author should be able to access {content.type} content edition page of its content.'
            )
        self.logout()

    def test_staff_can_access_content_edition_page(self):
        self.login(self.user_staff, 'hostel77')
        for content in self.contents.values():
            result = self.access_content_edition_page(self.kwargs_to_edit_contents[content])
            self.assertEqual(
                result.status_code,
                200,
                f'Staff should be able to access {content.type} content edition page even if he is not author.'
            )
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
            kwargs = {
                'description': 'new description',
                'introduction': 'new intro',
                'conclusion': 'new conclusion',
                'type': content.type,
                'licence': self.new_licence.pk,
                'subcategory': self.new_subcategory.pk,
                'last_hash': content.load_version().compute_hash()
            }
            self.kwargs_to_edit_contents[content] = kwargs

    def setUp(self):
        self.content_types = ['TUTORIAL', 'ARTICLE', 'OPINION']
        self.create_users()
        self.new_licence = LicenceFactory()
        self.new_subcategory = SubCategoryFactory()
        self.create_contents_set()
        self.create_kwargs_to_edit_contents()

    def assert_content_has_been_updated(self, content_pk, content_informations):
        content = PublishableContent.objects.get(pk=content_pk)
        self.assertEqual(content.title, content_informations['title'])
        self.assertEqual(content.description, content_informations['description'])
        self.assertEqual(content.licence.pk, content_informations['licence'])
        versioned = content.load_version()
        self.assertEqual(versioned.get_introduction(), content_informations['introduction'])
        self.assertEqual(versioned.get_conclusion(), content_informations['conclusion'])
        self.assertEqual(versioned.description, content_informations['description'])
        self.assertEqual(versioned.licence.pk, content_informations['licence'])

    def assert_content_has_not_been_updated(self, content_pk, content_informations):
        pass

    def test_public_cant_edit_content(self):
        for content in self.contents.values():
            kwargs = {'pk': content.pk, 'slug': content.slug}
            content_informations = self.kwargs_to_edit_contents[content]
            content_informations['title'] = content.title
            result = self.edit_content(kwargs, content_informations)
            self.assertEqual(
                result.status_code,
                302,
                f'Public should be redirected to login page if it tries to edit {content.type} content.'
            )
            self.assert_content_has_not_been_updated(content.pk, content_informations)

    def test_guest_cant_edit_content(self):
        self.login(self.user_guest, 'hostel77')
        for content in self.contents.values():
            kwargs = {'pk': content.pk, 'slug': content.slug}
            content_informations = self.kwargs_to_edit_contents[content]
            content_informations['title'] = content.title
            result = self.edit_content(kwargs, content_informations)
            self.assertEqual(
                result.status_code,
                403,
                f'Guest user should obtain an error if he tries to edit {content.type} content.'
            )
            self.assert_content_has_not_been_updated(content.pk, content_informations)
        self.logout()

    def test_read_only_author_cant_edit_content(self):
        self.login(self.user_read_only_author, 'hostel77')
        for content in self.contents.values():
            kwargs = {'pk': content.pk, 'slug': content.slug}
            content_informations = self.kwargs_to_edit_contents[content]
            content_informations['title'] = content.title
            result = self.edit_content(kwargs, content_informations)
            self.assertEqual(
                result.status_code,
                403,
                f'Read-only user should obtain an error if he tries to edit {content.type} content even if he is author.'
            )
            self.assert_content_has_not_been_updated(content.pk, content_informations)
        self.logout()

    def test_author_can_edit_content(self):
        self.login(self.user_author, 'hostel77')
        for content in self.contents.values():
            kwargs = {'pk': content.pk, 'slug': content.slug}
            content_informations = self.kwargs_to_edit_contents[content]
            content_informations['title'] = content.title
            result = self.edit_content(kwargs, content_informations)
            self.assertEqual(
                result.status_code,
                302,
                f'Author should be able to edit his {content.type} content.'
            )
            self.assert_content_has_been_updated(content.pk, content_informations)
        self.logout()

    def test_staff_can_edit_content(self):
        self.login(self.user_staff, 'hostel77')
        for content in self.contents.values():
            kwargs = {'pk': content.pk, 'slug': content.slug}
            content_informations = self.kwargs_to_edit_contents[content]
            content_informations['title'] = content.title
            result = self.edit_content(kwargs, content_informations)
            self.assertEqual(
                result.status_code,
                302,
                f'Staff should be able to edit {content.type} content even if he is not author.'
            )
            self.assert_content_has_been_updated(content.pk, content_informations)
        self.logout()

    def test_edition_with_new_title(self):
        self.login(self.user_staff, 'hostel77')
        for content in self.contents.values():
            kwargs = {'pk': content.pk, 'slug': content.slug}
            content_informations = self.kwargs_to_edit_contents[content]
            content_informations['title'] = 'new_title'
            result = self.edit_content(kwargs, content_informations)
            self.assertEqual(
                result.status_code,
                302,
                f'Author should be able to edit his {content.type} content and edit the title.'
            )
            self.assert_content_has_been_updated(content.pk, content_informations)
            versioned = PublishableContent.objects.get(pk=content.pk)
            self.assertNotEqual(
                versioned.slug,
                content.slug,
                f'The #{content.type} content slug should have changed since its title has been modified.'
            )
            self.assertEqual(
                self.access_content_display_page({'pk': content.pk, 'slug': content.slug}).status_code,
                404,
                f'Author should not be able to access its {content.type} content using old slug.'
            )
            self.assertEqual(
                self.access_content_display_page({'pk': content.pk, 'slug': versioned.slug}).status_code,
                200,
                f'Author should be able to access its {content.type} content using the new slug.'
            )
        self.logout()

    def test_edition_with_new_icon(self):
        self.login(self.user_staff, 'hostel77')
        for content in self.contents.values():
            kwargs = {'pk': content.pk, 'slug': content.slug}
            content_informations = self.kwargs_to_edit_contents[content]
            content_informations['title'] = content.title
            content_informations['image'] = open('{}/fixtures/noir_black.png'.format(settings.BASE_DIR), 'rb')
            result = self.edit_content(kwargs, content_informations)
            self.assertEqual(
                result.status_code,
                302,
                f'Author should be able to edit his {content.type} content and change its icon.'
            )
            self.assert_content_has_been_updated(content.pk, content_informations)
            # TO WRITE CHECK GALLERY
        self.logout()

    def test_edition_without_hash_fails(self):
        self.login(self.user_staff, 'hostel77')
        for content in self.contents.values():
            kwargs = {'pk': content.pk, 'slug': content.slug}
            content_informations = self.kwargs_to_edit_contents[content]
            content_informations['title'] = content.title
            content_informations['last_hash'] = ''
            result = self.edit_content(kwargs, content_informations)
            self.assertEqual(
                result.status_code,
                200,
                f'Edition should fails if it does not provides a correct hash.'
            )
            self.assert_content_has_not_been_updated(content.pk, content_informations)
        self.logout()




# @override_for_contents()
# class DisplayContainerTests(TutorialTestMixin, TestCase):

#     def setUp(self):
#         # TODO
#         # Only one content (a tutorial), opinions and articles
#         # does not have container
#         #
#         self.part_dic = {
#             'pk': self.tuto.pk,
#             'slug': self.tuto.slug
#             'container_slug': self.tuto.part1.slug
#         }
#         self.chapter_dic = {
#             'pk': self.tuto.pk,
#             'slug': self.tuto.slug,
#             'parent_container_slug': self.tuto.part1.slug,
#             'container_slug': self.tuto.part1.chapter.slug
#         }
#         self.kwargs_container = [part_dic, chapter_dic]

#     def access_container(self, kwargs):
#         return self.client.get(
#             reverse('content:view-container', kwargs=kwargs),
#             follow=False)

#     def test_public_cant_access_container(self):
#         "Redirect to connexion page."
#         result = access_container(self.part_dic)
#         for kwargs in self.kwargs_container
#             result = access_container(kwargs)
#             self.assertEqual(result.status_code, 302)

#     def test_guest_cant_access_container(self):
#         self.login(self.user_guest.username, 'hostel77')
#         for kwargs in self.kwargs_container
#             result = access_container(kwargs)
#             self.assertEqual(result.status_code, 403)
#         self.logout()

#     def test_ls_author_can_access_container(self):
#         self.login(self.user_ls_author.username, 'hostel77')
#         for kwargs in self.kwargs_container
#             result = access_container(kwargs)
#             self.assertEqual(result.status_code, 200)
#         self.logout()

#     def test_author_can_access_container(self):
#         self.login(self.user_author.username, 'hostel77')
#         for kwargs in self.kwargs_container
#             result = access_container(kwargs)
#             self.assertEqual(result.status_code, 200)
#         self.logout()

#     def test_staff_can_access_container(self):
#         self.login(self.user_staff.username, 'hostel77')
#         for kwargs in self.kwargs_container
#             result = access_container(kwargs)
#             self.assertEqual(result.status_code, 200)
#         self.logout()

# class ContainerCreationAccessTests(TutorialTestMixin, TestCase):
#     def setUp():
#         # Create a tuto with part
#         # Create an article and an opinion

# # Pour public, ls, auteur et guest.
# #     Tester accès à création container dans tuto vide.
# #     Tester accès à création container dans tuto avec partie.
# #     Tester accès à création container dans chapitre de tuto avec partie.
# #     Tester accès à création container dans tuto avec chapitres.
# #     Tester accès à création container dans article.
# #     Tester accès à création container dans opinion.
# #     Tester accès à création container dans tuto avec extrait.
# #     Tester accès à création container dans chapitre de tuto avec partie.
# #
# # dans Tuto vide  OK
# # dans tuto avec container  OK   => c'était
# # dans tuto avec extrait    NOK

# # dans level 1 container vide             OK => on rajoute un chapitre, ça devient une partie
# # dans level 1 container avec container   OK => c'était une partie on rajoute un chapitre
# # dans level 1 container avec extrait     NOK  c'était un chapitre

# # dans level 2 container vide ou pas        NOK  => c'est un chapitre
# # dans Article    NOK
# # dans Opinion    NOK
# #
# # La règle c'est que si tu es un conteneur de profondeur inférieur à la profondeur maximale - 1
# # et que tu ne contiens pas d'extraits, c'est OK.


#     def setUp()

#     self.slug_keys = ['parent_container_slug', 'container_slug']

#     def compute_kwargs_to_create_container_of_depth(self, depth, with_extract=False):
#         tuto = PublishableContentFactory(type='TUTORIAL')
#         tuto.authors.add(self.user_author)
#         tuto.save()
#         kwargs = {'pk' = tuto.pk, 'slug' = tuto.slug}
#         container = ContainerFactory(parent=tuto.load_version(), db_object=tuto)
#         for i in range(1, depth):
#             kwargs[self.slug_keys[depth - i]] = container.pk
#             container = ContainerFactory(parent=container, db_object=tuto)
#         ExtractFactory(container=container, db_object=tuto)
#         return kwargs

#     def compute_kwargs_to_create_container_of_depth_in_container_without_extract(self):
#         for depth in range(max_depth):
#             kwargs = self.compute_tuto_and_kwargs_to_create_container_of_depth(depth, with_extract=False)
#             self.kwargs_to_create_container_of_depth_in_container_without_extract[depth] = kwargs

#     def compute_kwargs_to_create_container_of_depth_in_container_with_extract(self):
#         for depth in range(max_depth):
#             kwargs = self.compute_tuto_and_kwargs_to_create_container_of_depth(depth, with_extract=True)
#             self.kwargs_to_create_container_of_depth_in_container_without_extract[depth] = kwargs


#     def test_public_cant_access_container_creation_page(self):
#         for depth in range(max_depth - 1):
#             result = access_container_creation_page(self.kwargs_without_extract_of_depth[depth])
#             self.assertEqual(result, 302)

#     # Faire la même chose pour with extract


# # Faire la même chose pour l'utilisation de la page associée

#     def access_container_creation_page(self, kwargs):
#         return self.client.post(
#             reverse('content:create-container', kwargs),
#             follow=False)

#     # COMMENT TO WRITE

#     def test_public_cant_access_void_tuto_creation_container_page(self):
#         result = access_container_creation_page(void_tuto_creation_container_kwargs)
#         self.assertEqual(result.status_code, 302)

#     def test_guest_cant_access_void_tuto_creation_container(self):
#         self.login(self.user_guest.username, 'hostel77')
#         result = access_container_creation_page(void_tuto_creation_container_kwargs)
#         self.assertEqual(result.status_code, 403)
#         self.logout()

#     def test_ls_author_cant_access_void_tuto_creation_container(self):
#         self.login(self.user_ls_author.username, 'hostel77')
#         result = access_container_creation_page(void_tuto_creation_container_kwargs)
#         self.assertEqual(result.status_code, 403)
#         self.logout()

#     def test_author_can_access_void_tuto_creation_container(self):
#         self.login(self.user_author.username, 'hostel77')
#         result = access_container_creation_page(void_tuto_creation_container_kwargs)
#         self.assertEqual(result.status_code, 200)
#         self.logout()

#     def test_staff_can_access_void_tuto_creation_container(self):
#         self.login(self.user_staff.username, 'hostel77')
#         result = access_container_creation_page(void_tuto_creation_container_kwargs)
#         self.assertEqual(result.status_code, 200)
#         self.logout()

#     # COMMENT TO WRITE

#     def test_public_cant_access_part_creation_page_of_tuto_with_part(self):
#         result = access_container_creation_page(part_creation_of_tuto_with_part_kwargs)
#         self.assertEqual(result.status_code, 302)

#     def test_guest_cant_access_part_creation_page_of_tuto_with_part(self):
#         self.login(self.user_guest.username, 'hostel77')
#         result = access_container_creation_page(part_creation_page_of_tuto_with_part_kwargs)
#         self.assertEqual(result.status_code, 403)
#         self.logout()

#     def test_ls_author_cant_access_part_creation_page_of_tuto_with_part(self):
#         self.login(self.user_ls_author.username, 'hostel77')
#         result = access_container_creation_page(part_creation_page_of_tuto_with_part_kwargs)
#         self.assertEqual(result.status_code, 403)
#         self.logout()

#     def test_author_can_access_part_creation_page_of_tuto_with_part(self):
#         self.login(self.user_author.username, 'hostel77')
#         result = access_container_creation_page(part_creation_page_of_tuto_with_part_kwargs)
#         self.assertEqual(result.status_code, 200)
#         self.logout()

#     def test_staff_can_access_part_creation_page_of_tuto_with_part(self):
#         self.login(self.user_staff.username, 'hostel77')
#         result = access_container_creation_page(part_creation_page_of_tuto_with_part_kwargs)
#         self.assertEqual(result.status_code, 200)
#         self.logout()

#     # COMMENT TO WRITE
#     def test_public_cant_access_chapter_creation_page_of_part_of_tuto_with_part(self):
#         result = access_container_creation_page(chapter_creation_page_of_part_of_tuto_with_part_kwargs)
#         self.assertEqual(result.status_code, 302)

#     def test_guest_cant_access_chapter_creation_page_of_part_of_tuto_with_part(self):
#         self.login(self.user_guest.username, 'hostel77')
#         result = access_container_creation_page(chapter_creation_page_of_part_of_tuto_with_part_kwargs)
#         self.assertEqual(result.status_code, 403)
#         self.logout()

#     def test_ls_author_cant_access_chapter_creation_page_of_part_of_tuto_with_part(self):
#         self.login(self.user_ls_author.username, 'hostel77')
#         result = access_container_creation_page(chapter_creation_page_of_part_of_tuto_with_part_kwargs)
#         self.assertEqual(result.status_code, 403)
#         self.logout()

#     def test_author_can_access_chapter_creation_page_of_part_of_tuto_with_part(self):
#         self.login(self.user_author.username, 'hostel77')
#         result = access_container_creation_page(chapter_creation_page_of_part_of_tuto_with_part_kwargs)
#         self.assertEqual(result.status_code, 200)
#         self.logout()

#     def test_staff_can_access_chapter_creation_page_of_part_of_tuto_with_part(self):
#         self.login(self.user_staff.username, 'hostel77')
#         result = access_container_creation_page(chapter_creation_page_of_part_of_tuto_with_part_kwargs)
#         self.assertEqual(result.status_code, 200)
#         self.logout()


#     # COMMENT TO WRITE
#     def test_public_cant_access_chapter_creation_page_of_tuto_with_chapter(self):
#         result = access_container_creation_page(chapter_creation_page_of_tuto_with_chapter_kwargs)
#         self.assertEqual(result.status_code, 302)

#     def test_guest_cant_access_chapter_creation_page_of_tuto_with_chapter(self):
#         self.login(self.user_guest.username, 'hostel77')
#         result = access_container_creation_page(chapter_creation_page_of_tuto_with_chapter_kwargs)
#         self.assertEqual(result.status_code, 403)
#         self.logout()

#     def test_ls_author_cant_access_chapter_creation_page_of_tuto_with_chapter(self):
#         self.login(self.user_ls_author.username, 'hostel77')
#         result = access_container_creation_page(chapter_creation_page_of_tuto_with_chapter_kwargs)
#         self.assertEqual(result.status_code, 403)
#         self.logout()

#     def test_author_can_access_chapter_creation_page_of_tuto_with_chapter(self):
#         self.login(self.user_author.username, 'hostel77')
#         result = access_container_creation_page(chapter_creation_page_of_tuto_with_chapter_kwargs)
#         self.assertEqual(result.status_code, 200)
#         self.logout()

#     def test_staff_can_access_chapter_creation_page_of_tuto_with_chapter(self):
#         self.login(self.user_staff.username, 'hostel77')
#         result = access_container_creation_page(chapter_creation_page_of_tuto_with_chapter_kwargs)
#         self.assertEqual(result.status_code, 200)
#         self.logout()

#     # COMMENT TO WRITE
#     def test_public_cant_access_container_creation_page_of_article(self):
#         result = access_container_creation_page(container_creation_page_of_article_kwargs)
#         self.assertEqual(result.status_code, 302)

#     def test_guest_cant_access_container_creation_page_of_article(self):
#         self.login(self.user_guest.username, 'hostel77')
#         result = access_container_creation_page(container_creation_page_of_article_kwargs)
#         self.assertEqual(result.status_code, 403)
#         self.logout()

#     def test_ls_author_cant_access_container_creation_page_of_article(self):
#         self.login(self.user_ls_author.username, 'hostel77')
#         result = access_container_creation_page(container_creation_page_of_article_kwargs)
#         self.assertEqual(result.status_code, 403)
#         self.logout()

#     def test_author_can_access_container_creation_page_of_article(self):
#         self.login(self.user_author.username, 'hostel77')
#         result = access_container_creation_page(container_creation_page_of_article_kwargs)
#         self.assertEqual(result.status_code, 403)
#         self.logout()

#     def test_staff_can_access_container_creation_page_of_article(self):
#         self.login(self.user_staff.username, 'hostel77')
#         result = access_container_creation_page(container_creation_page_of_article_kwargs)
#         self.assertEqual(result.status_code, 403)
#         self.logout()


#     # COMMENT TO WRITE
#     def test_public_cant_access_container_creation_page_of_opinion(self):
#         result = access_container_creation_page(container_creation_page_of_opinion_kwargs)
#         self.assertEqual(result.status_code, 302)

#     def test_guest_cant_access_container_creation_page_of_opinion(self):
#         self.login(self.user_guest.username, 'hostel77')
#         result = access_container_creation_page(container_creation_page_of_opinion_kwargs)
#         self.assertEqual(result.status_code, 403)
#         self.logout()

#     def test_ls_author_cant_access_container_creation_page_of_opinion(self):
#         self.login(self.user_ls_author.username, 'hostel77')
#         result = access_container_creation_page(container_creation_page_of_opinion_kwargs)
#         self.assertEqual(result.status_code, 403)
#         self.logout()

#     def test_author_can_access_container_creation_page_of_opinion(self):
#         self.login(self.user_author.username, 'hostel77')
#         result = access_container_creation_page(container_creation_page_of_opinion_kwargs)
#         self.assertEqual(result.status_code, 403)
#         self.logout()

#     def test_staff_can_access_container_creation_page_of_opinion(self):
#         self.login(self.user_staff.username, 'hostel77')
#         result = access_container_creation_page(container_creation_page_of_opinion_kwargs)
#         self.assertEqual(result.status_code, 403)
#         self.logout()


