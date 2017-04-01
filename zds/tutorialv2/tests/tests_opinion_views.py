# coding: utf-8
import shutil

import os
from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings

from zds.gallery.factories import UserGalleryFactory
from zds.member.factories import ProfileFactory, StaffProfileFactory
from zds.settings import BASE_DIR
from zds.tutorialv2.factories import PublishableContentFactory, ExtractFactory, LicenceFactory, PublishedContentFactory
from zds.tutorialv2.models.models_database import PublishableContent
from zds.utils.models import Alert

overrided_zds_app = settings.ZDS_APP
overrided_zds_app['content']['repo_private_path'] = os.path.join(BASE_DIR, 'contents-private-test')
overrided_zds_app['content']['repo_public_path'] = os.path.join(BASE_DIR, 'contents-public-test')
overrided_zds_app['content']['extra_content_generation_policy'] = "NONE"


@override_settings(ZDS_APP=overrided_zds_app)
class PublishedContentTests(TestCase):
    def setUp(self):
        overrided_zds_app['member']['bot_account'] = ProfileFactory().user.username
        self.licence = LicenceFactory()
        overrided_zds_app['content']['default_licence_pk'] = LicenceFactory().pk
        self.user_author = ProfileFactory().user
        self.user_staff = StaffProfileFactory().user
        self.user_guest = ProfileFactory().user

    def test_opinion_publication_author(self):
        """
        Test the publication of PublishableContent where type is OPINION (with author).
        """

        text_publication = u'Aussi tôt dit, aussi tôt fait !'

        opinion = PublishableContentFactory(type='OPINION')

        opinion.authors.add(self.user_author)
        UserGalleryFactory(gallery=opinion.gallery, user=self.user_author, mode='W')
        opinion.licence = self.licence
        opinion.save()

        opinion_draft = opinion.load_version()
        ExtractFactory(container=opinion_draft, db_object=opinion)
        ExtractFactory(container=opinion_draft, db_object=opinion)

        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)

        result = self.client.post(
            reverse('validation:publish-opinion', kwargs={'pk': opinion.pk, 'slug': opinion.slug}),
            {
                'text': text_publication,
                'source': '',
                'version': opinion.load_version().current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

    def test_accessible_ui_for_author(self):
        opinion = PublishedContentFactory(author_list=[self.user_author], type="OPINION")
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)
        resp = self.client.get(reverse("opinion:view", kwargs={"pk": opinion.pk, "slug": opinion.slug}))
        self.assertContains(resp, "Version brouillon", msg_prefix="Author must access their draft directly")

    def test_no_help_for_tribune(self):
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)
        resp = self.client.get(reverse("content:create-opinion"))
        self.assertNotContains(resp, 'id="div_id_helps"', msg_prefix="help field must not be displayed")

    def test_help_for_article(self):
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)
        resp = self.client.get(reverse("content:create-article"))
        self.assertEqual(200, resp.status_code)
        self.assertContains(resp, 'id="div_id_helps"', msg_prefix="help field must be displayed")

    def test_opinion_publication_staff(self):
        """
        Test the publication of PublishableContent where type is OPINION (with staff).
        """

        text_publication = u'Aussi tôt dit, aussi tôt fait !'

        opinion = PublishableContentFactory(type='OPINION')

        opinion.authors.add(self.user_author)
        UserGalleryFactory(gallery=opinion.gallery, user=self.user_author, mode='W')
        opinion.licence = self.licence
        opinion.save()

        opinion_draft = opinion.load_version()
        ExtractFactory(container=opinion_draft, db_object=opinion)
        ExtractFactory(container=opinion_draft, db_object=opinion)

        self.assertEqual(
            self.client.login(
                username=self.user_staff.username,
                password='hostel77'),
            True)

        result = self.client.post(
            reverse('validation:publish-opinion', kwargs={'pk': opinion.pk, 'slug': opinion.slug}),
            {
                'text': text_publication,
                'source': '',
                'version': opinion.load_version().current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

    def test_opinion_publication_guest(self):
        """
        Test the publication of PublishableContent where type is OPINION (with guest => 403).
        """

        text_publication = u'Aussi tôt dit, aussi tôt fait !'

        opinion = PublishableContentFactory(type='OPINION')

        opinion.authors.add(self.user_author)
        UserGalleryFactory(gallery=opinion.gallery, user=self.user_author, mode='W')
        opinion.licence = self.licence
        opinion.save()

        opinion_draft = opinion.load_version()
        ExtractFactory(container=opinion_draft, db_object=opinion)
        ExtractFactory(container=opinion_draft, db_object=opinion)

        self.assertEqual(
            self.client.login(
                username=self.user_guest.username,
                password='hostel77'),
            True)

        result = self.client.post(
            reverse('validation:publish-opinion', kwargs={'pk': opinion.pk, 'slug': opinion.slug}),
            {
                'text': text_publication,
                'source': '',
                'version': opinion.load_version().current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 403)

    def test_opinion_unpublication(self):
        """
        Test the unpublication of PublishableContent where type is OPINION (with author).
        """

        text_publication = u'Aussi tôt dit, aussi tôt fait !'
        text_unpublication = u'Au revoir !'

        opinion = PublishableContentFactory(type='OPINION')

        opinion.authors.add(self.user_author)
        UserGalleryFactory(gallery=opinion.gallery, user=self.user_author, mode='W')
        opinion.licence = self.licence
        opinion.save()

        opinion_draft = opinion.load_version()
        ExtractFactory(container=opinion_draft, db_object=opinion)
        ExtractFactory(container=opinion_draft, db_object=opinion)

        # author

        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)

        # publish
        result = self.client.post(
            reverse('validation:publish-opinion', kwargs={'pk': opinion.pk, 'slug': opinion.slug}),
            {
                'text': text_publication,
                'source': '',
                'version': opinion.load_version().current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        # unpublish
        result = self.client.post(
            reverse('validation:unpublish-opinion', kwargs={'pk': opinion.pk, 'slug': opinion.slug}),
            {
                'text': text_unpublication,
                'source': '',
                'version': opinion.load_version().current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        # staff

        self.assertEqual(
            self.client.login(
                username=self.user_staff.username,
                password='hostel77'),
            True)

        # publish
        result = self.client.post(
            reverse('validation:publish-opinion', kwargs={'pk': opinion.pk, 'slug': opinion.slug}),
            {
                'text': text_publication,
                'source': '',
                'version': opinion.load_version().current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        # unpublish
        result = self.client.post(
            reverse('validation:unpublish-opinion', kwargs={'pk': opinion.pk, 'slug': opinion.slug}),
            {
                'text': text_unpublication,
                'source': '',
                'version': opinion.load_version().current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        # guest => 403

        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)

        # publish with author
        result = self.client.post(
            reverse('validation:publish-opinion', kwargs={'pk': opinion.pk, 'slug': opinion.slug}),
            {
                'text': text_publication,
                'source': '',
                'version': opinion.load_version().current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        self.assertEqual(
            self.client.login(
                username=self.user_guest.username,
                password='hostel77'),
            True)

        # unpublish
        result = self.client.post(
            reverse('validation:unpublish-opinion', kwargs={'pk': opinion.pk, 'slug': opinion.slug}),
            {
                'text': text_unpublication,
                'source': '',
                'version': opinion.load_version().current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 403)

    def test_opinion_validation(self):
        """
        Test the validation of PublishableContent where type is OPINION.
        """

        text_publication = u'Aussi tôt dit, aussi tôt fait !'

        opinion = PublishableContentFactory(type='OPINION')

        opinion.authors.add(self.user_author)
        UserGalleryFactory(gallery=opinion.gallery, user=self.user_author, mode='W')
        opinion.licence = self.licence
        opinion.save()

        opinion_draft = opinion.load_version()
        ExtractFactory(container=opinion_draft, db_object=opinion)
        ExtractFactory(container=opinion_draft, db_object=opinion)

        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)

        # publish
        result = self.client.post(
            reverse('validation:publish-opinion', kwargs={'pk': opinion.pk, 'slug': opinion.slug}),
            {
                'text': text_publication,
                'source': '',
                'version': opinion.load_version().current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        # valid with author => 403
        opinion = PublishableContent.objects.get(pk=opinion.pk)
        opinion_draft = opinion.load_version()

        result = self.client.post(
            reverse('validation:pick-opinion', kwargs={'pk': opinion.pk, 'slug': opinion.slug}),
            {
                'source': '',
                'version': opinion_draft.current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 403)

        opinion = PublishableContent.objects.get(pk=opinion.pk)
        self.assertIsNone(opinion.sha_picked)
        self.assertIsNone(opinion.picked_date)

        self.assertEqual(
            self.client.login(
                username=self.user_staff.username,
                password='hostel77'),
            True)

        # valid with staff
        result = self.client.post(
            reverse('validation:pick-opinion', kwargs={'pk': opinion.pk, 'slug': opinion.slug}),
            {
                'source': '',
                'version': opinion_draft.current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        opinion = PublishableContent.objects.get(pk=opinion.pk)
        self.assertEqual(opinion.sha_picked, opinion_draft.current_version)
        self.assertIsNotNone(opinion.picked_date)

        # invalid with author => 403
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)

        result = self.client.post(
            reverse('validation:unpick-opinion', kwargs={'pk': opinion.pk, 'slug': opinion.slug}),
            {
                'text': u'Parce que je veux',
                'version': opinion_draft.current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 403)

        opinion = PublishableContent.objects.get(pk=opinion.pk)
        self.assertEqual(opinion.sha_picked, opinion_draft.current_version)

        # invalid with staff
        self.assertEqual(
            self.client.login(
                username=self.user_staff.username,
                password='hostel77'),
            True)

        result = self.client.post(
            reverse('validation:unpick-opinion', kwargs={'pk': opinion.pk, 'slug': opinion.slug}),
            {
                'text': u'Parce que je peux !',
                'version': opinion_draft.current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        opinion = PublishableContent.objects.get(pk=opinion.pk)
        self.assertIsNone(opinion.sha_picked)

        # double invalidation wont work
        result = self.client.post(
            reverse('validation:unpick-opinion', kwargs={'pk': opinion.pk, 'slug': opinion.slug}),
            {
                'text': u'Parce que je peux toujours ...',
                'version': opinion_draft.current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 403)

    def test_opinion_conversion(self):
        """
        Test the conversion of PublishableContent with type=OPINION
        to PublishableContent with type=ARTICLE
        """

        text_publication = u'Aussi tôt dit, aussi tôt fait !'

        opinion = PublishableContentFactory(type='OPINION')

        opinion.authors.add(self.user_author)
        UserGalleryFactory(gallery=opinion.gallery, user=self.user_author, mode='W')
        opinion.licence = self.licence
        opinion.save()

        opinion_draft = opinion.load_version()
        ExtractFactory(container=opinion_draft, db_object=opinion)
        ExtractFactory(container=opinion_draft, db_object=opinion)

        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)

        # publish
        result = self.client.post(
            reverse('validation:publish-opinion', kwargs={'pk': opinion.pk, 'slug': opinion.slug}),
            {
                'text': text_publication,
                'source': '',
                'version': opinion.load_version().current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        # valid with author => 403
        result = self.client.post(
            reverse('validation:promote-opinion', kwargs={'pk': opinion.pk, 'slug': opinion.slug}),
            {
                'source': '',
                'version': opinion.load_version().current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 403)

        self.assertEqual(
            self.client.login(
                username=self.user_staff.username,
                password='hostel77'),
            True)

        # valid with staff
        result = self.client.post(
            reverse('validation:promote-opinion', kwargs={'pk': opinion.pk, 'slug': opinion.slug}),
            {
                'source': '',
                'version': opinion.load_version().current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

    def test_opinion_alert(self):
        """Test content alert"""

        text_publication = u'Aussi tôt dit, aussi tôt fait !'

        opinion = PublishableContentFactory(type='OPINION')

        opinion.authors.add(self.user_author)
        UserGalleryFactory(gallery=opinion.gallery, user=self.user_author, mode='W')
        opinion.licence = self.licence
        opinion.save()

        opinion_draft = opinion.load_version()
        ExtractFactory(container=opinion_draft, db_object=opinion)
        ExtractFactory(container=opinion_draft, db_object=opinion)

        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)

        result = self.client.post(
            reverse('validation:publish-opinion', kwargs={'pk': opinion.pk, 'slug': opinion.slug}),
            {
                'text': text_publication,
                'source': '',
                'version': opinion.load_version().current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        # Alert content
        random_user = ProfileFactory().user

        self.assertEqual(
            self.client.login(
                username=random_user.username,
                password='hostel77'),
            True)

        result = self.client.post(
            reverse('content:alert-content', kwargs={'pk': opinion.pk}),
            {
                "signal_text": u'Yeurk !'
            }, follow=False
        )

        self.assertEqual(result.status_code, 302)
        self.assertIsNotNone(Alert.objects.filter(author__pk=random_user.pk, content__pk=opinion.pk).first())

        alert = Alert.objects.filter(author__pk=random_user.pk, content__pk=opinion.pk).first()
        self.assertFalse(alert.solved)

        result = self.client.post(
            reverse('content:resolve-content', kwargs={'pk': opinion.pk}),
            {
                "alert_pk": alert.pk,
                "text": u'Je peux ?'
            }, follow=False
        )
        self.assertEqual(result.status_code, 403)  # solving the alert by yourself wont work

        alert = Alert.objects.get(pk=alert.pk)
        self.assertFalse(alert.solved)

        self.assertEqual(
            self.client.login(
                username=self.user_staff.username,
                password='hostel77'),
            True)

        result = self.client.post(
            reverse('content:resolve-content', kwargs={'pk': opinion.pk}),
            {
                "alert_pk": alert.pk,
                "text": u'Anéfé!'
            }, follow=False
        )
        self.assertEqual(result.status_code, 302)

        alert = Alert.objects.get(pk=alert.pk)
        self.assertTrue(alert.solved)

    def tearDown(self):

        if os.path.isdir(settings.ZDS_APP['content']['repo_private_path']):
            shutil.rmtree(settings.ZDS_APP['content']['repo_private_path'])
        if os.path.isdir(settings.ZDS_APP['content']['repo_public_path']):
            shutil.rmtree(settings.ZDS_APP['content']['repo_public_path'])
        if os.path.isdir(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)

        # re-activate PDF build
        settings.ZDS_APP['content']['build_pdf_when_published'] = True
