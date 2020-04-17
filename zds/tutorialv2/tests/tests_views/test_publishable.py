# Tests contents.py view

def login(self, user, password):
    success = self.client.login(username, password)
    self.assertEqual(success, True)

@override_for_contents()
class ContentDisplayTests(TutorialTestMixin, TestCase):

    def setUp(self):

    def access_content(self):
        return self.client.get(
            reverse('content:view', args=[self.tuto.pk, self.tuto.slug]),
            follow=False)

    def test_author_can_access_to_content(self):
        self.login(self.user_author.username, 'hostel77')
        result = access_content()
        self.assertEqual(result.status_code, 200)
        self.logout()

    def test_public_cant_access_to_content(self):
        result = access_content()
        self.assertEqual(result.status_code, 302)

    def test_guest_can_access_to_content(self):
        self.login(self.user_guest.username, 'hostel77')
        result = access_content()
        self.assertEqual(result.status_code, 403)
        self.logout()

    def test_staff_can_access_to_content(self):
        self.login(self.user_staff.username, 'hostel77')
        result = access_content()
        self.assertEqual(result.status_code, 200)
        self.logout()


@override_for_contents()
class ParentContainerDisplayTests(TutorialTestMixin, TestCase):

    def setUp(self):

    def access_part(self):
        return self.client.get(
            reverse('content:view-container',
                    kwargs={
                        'pk': self.tuto.pk,
                        'slug': self.tuto.slug
                        'container_slug': self.tuto.part1.slug
                    }),
            follow=False)

    def test_author_can_access_to_part(self):
        self.login(self.user_author.username, 'hostel77')
        result = access_part()
        self.assertEqual(result.status_code, 200)
        self.logout()

    def test_public_cant_access_to_part(self):
        "Redirect to connexion page."
        result = access_part()
        self.assertEqual(result.status_code, 302)

    def test_guest_can_access_to_part(self):
        self.login(self.user_guest.username, 'hostel77')
        result = access_part()
        self.assertEqual(result.status_code, 403)
        self.logout()

    def test_staff_can_access_to_part(self):
        self.login(self.user_staff.username, 'hostel77')
        result = access_part()
        self.assertEqual(result.status_code, 200)
        self.logout()


@override_for_contents()
class ContainerDisplayTests(TutorialTestMixin, TestCase):

    def setUp(self):

    def access_chapter(self):
        return self.client.get(
            reverse('content:view-container',
                    kwargs={
                        'pk': self.tuto.pk,
                        'slug': self.tuto.slug,
                        'parent_container_slug': self.tuto.part1.slug,
                        'container_slug': self.tuto.part1.chapter.slug
                    }),
            follow=False)

    def test_author_can_access_to_chapter(self):
        self.login(self.user_author.username, 'hostel77')
        result = access_chapter()
        self.assertEqual(result.status_code, 200)
        self.logout()

    def test_public_cant_access_to_chapter(self):
        "Redirect to connexion page."
        result = access_chapter()
        self.assertEqual(result.status_code, 302)

    def test_guest_can_access_to_chapter(self):
        self.login(self.user_guest.username, 'hostel77')
        result = access_chapter()
        self.assertEqual(result.status_code, 403)
        self.logout()

    def test_staff_can_access_to_chapter(self):
        self.login(self.user_staff.username, 'hostel77')
        result = access_chapter()
        self.assertEqual(result.status_code, 200)
        self.logout()



class CreationContentTest(TutorialTestMixin, TestCase):
    def setUp():
        self.dic = {
            'title': 'un titre',
            'description': 'une description',
            'introduction': 'une intro',
            'conclusion': 'une conclusion',
            'type': 'TUTORIAL',
            'licence': self.licence.pk,
            'subcategory': self.subcategory.pk,
            'image': open('{}/fixtures/noir_black.png'.format(settings.BASE_DIR), 'rb')
        }

    def test_access_content_creation_page(self):
        return self.client.post(
            reverse('content:create-tutorial'),
            follow=False)

    def test_registered_user_can_access_to_creation_page(self):
        self.login(self.user_author.username, 'hostel77')
        result = access_content_creation_page()
        self.assertEqual(result.status_code, 200)
        self.logout()

    def test_staff_user_can_access_to_creation_page(self):
        self.login(self.user_author.username, 'hostel77')
        result = access_content_creation_page()
        self.assertEqual(result.status_code, 200)
        self.logout()

    def test_user_ls_cant_access_to_creation_page(self):
        self.login(self.user_ls.username, 'hostel77')
        result = access_content_creation_page()
        self.assertEqual(result.status_code, 403)
        self.logout()

    def test_public_cant_access_to_creation_page(self):
        "Redirect to connexion page."
        self.login(self.user_author.username, 'hostel77')
        result = access_content_creation_page()
        self.assertEqual(result.status_code, 302)
        self.logout()


    def create_content(self):
        return self.client.post(
            reverse('content:create-tutorial', dic),
            follow=False
        )

    def test_registered_user_can_create_content(self):
        self.login(self.user_author.username, 'hostel77')
        self.assertEqual(create_content().status_code, 200)
        self.logout()

    def test_staff_user_can_create_content(self):
        self.login(self.user_author.username, 'hostel77')
        self.assertEqual(create_content().status_code, 200)
        self.logout()

    def test_user_ls_cant_create_content(self):
        self.login(self.user_ls.username, 'hostel77')
        self.assertEqual(create_content().status_code, 403)
        self.logout()

    def test_public_cant_create_content(self):
        "Redirect to connexion page."
        self.login(self.user_author.username, 'hostel77')
        self.assertEqual(create_content().status_code, 302)
        self.logout()

    def test_creation_add_content_to_db(self):
        old_content_number = PublishableContent.objects.all().count()
        self.login(self.user_author.username, 'hostel77')
        self.assertEqual(create_content().status_code, 302)
        content_number = PublishableContent.objects.all().count()
        self.assertEqual(content_number, old_content_number + 1)
        self.logout()

    def test_creation_add_content_to_db(self):
        old_content_number = PublishableContent.objects.all().count()
        self.login(self.user_author.username, 'hostel77')
        self.assertEqual(create_content().status_code, 302)
        content_number = PublishableContent.objects.all().count()
        self.assertEqual(content_number, old_content_number + 1)
        self.logout()

    def test_creation_set_author_correctly(self):
        self.login(self.user_author.username, 'hostel77')
        self.assertEqual(create_content().status_code, 302)
        tuto = PublishableContent.objects.last()
        self.assertIn(self.user_author, tuto.authors)
        self.assertEqual(tuto.authors.count(), 1)
        self.logout()

    def test_icon_is_in_gallery(self):
        self.login(self.user_author.username, 'hostel77')
        self.assertEqual(create_content().status_code, 302)
        tuto = PublishableContent.objects.last()
        pk = tuto.pk
        slug = tuto.slug
        versioned = tuto.load_version()
        self.assertEqual(Gallery.objects.filter(pk=tuto.gallery.pk).count(), 1)
        self.assertEqual(UserGallery.objects.filter(gallery__pk=tuto.gallery.pk).count(), tuto.authors.count())
        self.assertEqual(Image.objects.filter(gallery__pk=tuto.gallery.pk).count(), 1)
        self.logout()

    def test_preview_in_content_creation(self):
        self.login(self.user_author.username, 'hostel77')
        random_with_md = 'un text contenant du **markdown** .'
        response = self.client.post(
            reverse('content:create-tutorial'),
            {
                'text': random_with_md,
                'preview': '',
            }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)

        result_string = ''.join(str(a, 'utf-8') for a in response.streaming_content)
        self.assertIn('<strong>markdown</strong>', result_string, 'We need the text to be properly formatted')
        self.logout()