import os

import datetime
from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings
from django.utils.translation import ugettext_lazy as _

from zds.gallery.factories import UserGalleryFactory
from zds.member.factories import ProfileFactory, StaffProfileFactory
from zds.tutorialv2.factories import (PublishableContentFactory, ExtractFactory, LicenceFactory,
                                      PublishedContentFactory, SubCategoryFactory)
from zds.tutorialv2.models.database import PublishableContent, PublishedContent, PickListOperation
from zds.tutorialv2.tests import TutorialTestMixin
from zds.utils.models import Alert
from copy import deepcopy

overridden_zds_app = deepcopy(settings.ZDS_APP)
overridden_zds_app['content']['repo_private_path'] = os.path.join(settings.BASE_DIR, 'contents-private-test')
overridden_zds_app['content']['repo_public_path'] = os.path.join(settings.BASE_DIR, 'contents-public-test')
overridden_zds_app['content']['extra_content_generation_policy'] = 'NONE'


@override_settings(MEDIA_ROOT=os.path.join(settings.BASE_DIR, 'media-test'))
@override_settings(ZDS_APP=overridden_zds_app)
@override_settings(ES_ENABLED=False)
class PublishedContentTests(TestCase, TutorialTestMixin):
    def setUp(self):
        self.overridden_zds_app = overridden_zds_app
        overridden_zds_app['member']['bot_account'] = ProfileFactory().user.username
        self.licence = LicenceFactory()
        overridden_zds_app['content']['default_licence_pk'] = LicenceFactory().pk
        self.user_author = ProfileFactory().user
        self.user_staff = StaffProfileFactory().user
        self.user_guest = ProfileFactory().user

    def test_opinion_publication_author(self):
        """
        Test the publication of PublishableContent where type is OPINION (with author).
        """

        text_publication = 'Aussi tôt dit, aussi tôt fait !'

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
                'version': opinion_draft.current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        self.assertEqual(PublishedContent.objects.count(), 1)

        opinion = PublishableContent.objects.get(pk=opinion.pk)
        self.assertIsNotNone(opinion.public_version)
        self.assertEqual(opinion.public_version.sha_public, opinion_draft.current_version)

    def test_accessible_ui_for_author(self):
        opinion = PublishedContentFactory(author_list=[self.user_author], type='OPINION')
        subcategory = SubCategoryFactory()
        opinion.subcategory.add(subcategory)
        opinion.save()
        self.assertEqual(
            self.client.login(username=self.user_author.username, password='hostel77'),
            True)
        resp = self.client.get(reverse('opinion:view', kwargs={'pk': opinion.pk, 'slug': opinion.slug}))
        self.assertContains(resp, 'Version brouillon', msg_prefix='Author must access their draft directly')
        self.assertNotContains(resp, '{}?subcategory='.format(reverse('publication:list')))
        self.assertContains(resp, '{}?category='.format(reverse('opinion:list')))

    def test_no_help_for_tribune(self):
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)
        resp = self.client.get(reverse('content:create-opinion'))
        self.assertNotContains(resp, 'id="div_id_helps"', msg_prefix='help field must not be displayed')

    def test_help_for_article(self):
        self.assertEqual(
            self.client.login(
                username=self.user_author.username,
                password='hostel77'),
            True)
        resp = self.client.get(reverse('content:create-article'))
        self.assertEqual(200, resp.status_code)
        self.assertContains(resp, 'id="div_id_helps"', msg_prefix='help field must be displayed')

    def test_opinion_publication_staff(self):
        """
        Test the publication of PublishableContent where type is OPINION (with staff).
        """

        text_publication = 'Aussi tôt dit, aussi tôt fait !'

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
                'version': opinion_draft.current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        self.assertEqual(PublishedContent.objects.count(), 1)

        opinion = PublishableContent.objects.get(pk=opinion.pk)
        self.assertIsNotNone(opinion.public_version)
        self.assertEqual(opinion.public_version.sha_public, opinion_draft.current_version)

    def test_opinion_publication_guest(self):
        """
        Test the publication of PublishableContent where type is OPINION (with guest => 403).
        """

        text_publication = 'Aussi tôt dit, aussi tôt fait !'

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
                'version': opinion_draft.current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 403)

        self.assertEqual(PublishedContent.objects.count(), 0)

    def test_opinion_unpublication(self):
        """
        Test the unpublication of PublishableContent where type is OPINION (with author).
        """

        text_publication = 'Aussi tôt dit, aussi tôt fait !'
        text_unpublication = 'Au revoir !'

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
                'version': opinion_draft.current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        self.assertEqual(PublishedContent.objects.count(), 1)

        opinion = PublishableContent.objects.get(pk=opinion.pk)
        self.assertIsNotNone(opinion.public_version)
        self.assertEqual(opinion.public_version.sha_public, opinion_draft.current_version)

        # unpublish
        result = self.client.post(
            reverse('validation:unpublish-opinion', kwargs={'pk': opinion.pk, 'slug': opinion.slug}),
            {
                'text': text_unpublication,
                'source': '',
                'version': opinion_draft.current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        self.assertEqual(PublishedContent.objects.count(), 0)

        opinion = PublishableContent.objects.get(pk=opinion.pk)
        self.assertIsNone(opinion.public_version)

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
                'version': opinion_draft.current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        self.assertEqual(PublishedContent.objects.count(), 1)

        opinion = PublishableContent.objects.get(pk=opinion.pk)
        self.assertIsNotNone(opinion.public_version)
        self.assertEqual(opinion.public_version.sha_public, opinion_draft.current_version)

        # unpublish
        result = self.client.post(
            reverse('validation:unpublish-opinion', kwargs={'pk': opinion.pk, 'slug': opinion.slug}),
            {
                'text': text_unpublication,
                'source': '',
                'version': opinion_draft.current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        self.assertEqual(PublishedContent.objects.count(), 0)

        opinion = PublishableContent.objects.get(pk=opinion.pk)
        self.assertIsNone(opinion.public_version)

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
                'version': opinion_draft.current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        self.assertEqual(PublishedContent.objects.count(), 1)

        opinion = PublishableContent.objects.get(pk=opinion.pk)
        self.assertIsNotNone(opinion.public_version)
        self.assertEqual(opinion.public_version.sha_public, opinion_draft.current_version)

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
                'version': opinion_draft.current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 403)

        self.assertEqual(PublishedContent.objects.count(), 1)

    def test_opinion_validation(self):
        """
        Test the validation of PublishableContent where type is OPINION.
        """

        text_publication = 'Aussi tôt dit, aussi tôt fait !'

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
                'version': opinion_draft.current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        self.assertEqual(PublishedContent.objects.count(), 1)

        opinion = PublishableContent.objects.get(pk=opinion.pk)
        self.assertIsNotNone(opinion.public_version)
        self.assertEqual(opinion.public_version.sha_public, opinion_draft.current_version)

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
                'text': 'Parce que je veux',
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
                'text': 'Parce que je peux !',
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
                'text': 'Parce que je peux toujours ...',
                'version': opinion_draft.current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 403)

    def test_ignore_opinion(self):
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
                'source': '',
                'version': opinion_draft.current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        # ignore with author => 403
        result = self.client.post(
            reverse('validation:ignore-opinion', kwargs={'pk': opinion.pk, 'slug': opinion.slug}),
            {
                'operation': 'NO_PICK',
            },
            follow=False)
        self.assertEqual(result.status_code, 403)

        # now, login as staff
        self.assertEqual(
            self.client.login(
                username=self.user_staff.username,
                password='hostel77'),
            True)

        # check that the opinion is displayed
        result = self.client.get(reverse('validation:list-opinion'))
        self.assertContains(result, opinion.title)

        # ignore the opinion
        result = self.client.post(
            reverse('validation:ignore-opinion', kwargs={'pk': opinion.pk, 'slug': opinion.slug}),
            {
                'operation': 'NO_PICK',
            },
            follow=False)
        self.assertEqual(result.status_code, 200)

        # check that the opinion is not displayed
        result = self.client.get(reverse('validation:list-opinion'))
        self.assertNotContains(result, opinion.title)

        # publish the opinion again
        result = self.client.post(
            reverse('validation:publish-opinion', kwargs={'pk': opinion.pk, 'slug': opinion.slug}),
            {
                'source': '',
                'version': opinion_draft.current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        # check that the opinion is displayed
        result = self.client.get(reverse('validation:list-opinion'))
        self.assertContains(result, opinion.title)

        # reject it
        result = self.client.post(
            reverse('validation:ignore-opinion', kwargs={'pk': opinion.pk, 'slug': opinion.slug}),
            {
                'operation': 'REJECT',
            },
            follow=False)
        self.assertEqual(result.status_code, 200)

        # publish again
        result = self.client.post(
            reverse('validation:publish-opinion', kwargs={'pk': opinion.pk, 'slug': opinion.slug}),
            {
                'source': '',
                'version': opinion_draft.current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        # check that the opinion is not displayed
        result = self.client.get(reverse('validation:list-opinion'))
        self.assertNotContains(result, opinion.title)

    def test_permanently_unpublish_opinion(self):
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
                'source': '',
                'version': opinion_draft.current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        # login as staff
        self.assertEqual(
            self.client.login(
                username=self.user_staff.username,
                password='hostel77'),
            True)

        # unpublish opinion
        result = self.client.post(
            reverse('validation:ignore-opinion', kwargs={'pk': opinion.pk, 'slug': opinion.slug}),
            {
                'operation': 'REMOVE_PUB',
            },
            follow=False)
        self.assertEqual(result.status_code, 200)

        # refresh
        opinion = PublishableContent.objects.get(pk=opinion.pk)

        # check that the opinion is not published
        self.assertFalse(opinion.in_public())

        # check that it's impossible to publish the opinion again
        result = self.client.get(opinion.get_absolute_url())
        self.assertContains(result, _('Billet modéré'))  # front

        result = self.client.post(
            reverse('validation:publish-opinion', kwargs={'pk': opinion.pk, 'slug': opinion.slug}),
            {
                'source': '',
                'version': opinion_draft.current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 403)  # back

    def test_defenitely_unpublish_alerted_opinion(self):
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
                'source': '',
                'version': opinion_draft.current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        # login as staff
        self.assertEqual(
            self.client.login(
                username=self.user_staff.username,
                password='hostel77'),
            True)
        alerter = ProfileFactory().user
        Alert.objects.create(author=alerter, scope='CONTENT', content=opinion, pubdate=datetime.datetime.now(),
                             text="J'ai un probleme avec cette opinion : c'est pas la mienne.")
        # unpublish opinion
        result = self.client.post(
            reverse('validation:ignore-opinion', kwargs={'pk': opinion.pk, 'slug': opinion.slug}),
            {
                'operation': 'REMOVE_PUB',
            },
            follow=False)
        self.assertEqual(result.status_code, 200)

        # refresh
        opinion = PublishableContent.objects.get(pk=opinion.pk)

        # check that the opinion is not published
        self.assertFalse(opinion.in_public())

        # check that it's impossible to publish the opinion again
        result = self.client.get(opinion.get_absolute_url())
        self.assertContains(result, _('Billet modéré'))  # front

        result = self.client.post(
            reverse('validation:publish-opinion', kwargs={'pk': opinion.pk, 'slug': opinion.slug}),
            {
                'source': '',
                'version': opinion_draft.current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 403)  # back
        self.assertTrue(Alert.objects.filter(content=opinion).last().solved)
        # check alert page is still accessible and our alert is well displayed
        resp = self.client.get(reverse('pages-alerts'))
        self.assertEqual(200, resp.status_code)
        self.assertEqual(0, len(resp.context['alerts']))
        self.assertEqual(1, len(resp.context['solved']))

    def test_cancel_pick_operation(self):
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
                'source': '',
                'version': opinion_draft.current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        # login as staff
        self.assertEqual(
            self.client.login(
                username=self.user_staff.username,
                password='hostel77'),
            True)

        # PICK
        result = self.client.post(
            reverse('validation:pick-opinion', kwargs={'pk': opinion.pk, 'slug': opinion.slug}),
            {
                'source': '',
                'version': opinion_draft.current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        # cancel the operation
        operation = PickListOperation.objects.latest('operation_date')
        result = self.client.post(
            reverse('validation:revoke-ignore-opinion', kwargs={'pk': operation.pk}),
            follow=False)
        self.assertEqual(result.status_code, 200)

        # refresh
        operation = PickListOperation.objects.get(pk=operation.pk)
        opinion = PublishableContent.objects.get(pk=opinion.pk)
        self.assertFalse(operation.is_effective)
        self.assertEqual(self.user_staff, operation.canceler_user)
        self.assertIsNone(opinion.sha_picked)

        # NO_PICK
        result = self.client.post(
            reverse('validation:ignore-opinion', kwargs={'pk': opinion.pk, 'slug': opinion.slug}),
            {
                'operation': 'NO_PICK',
            },
            follow=False)
        self.assertEqual(result.status_code, 200)

        # cancel the operation
        operation = PickListOperation.objects.latest('operation_date')
        result = self.client.post(
            reverse('validation:revoke-ignore-opinion', kwargs={'pk': operation.pk}),
            follow=False)
        self.assertEqual(result.status_code, 200)

        # check that the opinion is displayed on validation page
        result = self.client.get(reverse('validation:list-opinion'))
        self.assertContains(result, opinion.title)

        # REMOVE_PUB
        result = self.client.post(
            reverse('validation:ignore-opinion', kwargs={'pk': opinion.pk, 'slug': opinion.slug}),
            {
                'operation': 'REMOVE_PUB',
            },
            follow=False)
        self.assertEqual(result.status_code, 200)

        # cancel the operation
        operation = PickListOperation.objects.latest('operation_date')
        result = self.client.post(
            reverse('validation:revoke-ignore-opinion', kwargs={'pk': operation.pk}),
            follow=False)
        self.assertEqual(result.status_code, 200)

        # check that the opinion can be published again
        result = self.client.post(
            reverse('validation:publish-opinion', kwargs={'pk': opinion.pk, 'slug': opinion.slug}),
            {
                'source': '',
                'version': opinion_draft.current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

    def test_opinion_conversion(self):
        """
        Test the conversion of PublishableContent with type=OPINION
        to PublishableContent with type=ARTICLE
        """

        text_publication = 'Aussi tôt dit, aussi tôt fait !'

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
                'version': opinion_draft.current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        self.assertEqual(PublishedContent.objects.count(), 1)

        opinion = PublishableContent.objects.get(pk=opinion.pk)
        self.assertIsNotNone(opinion.public_version)
        self.assertEqual(opinion.public_version.sha_public, opinion_draft.current_version)

        # valid with author => 403
        result = self.client.post(
            reverse('validation:promote-opinion', kwargs={'pk': opinion.pk, 'slug': opinion.slug}),
            {
                'source': '',
                'version': opinion_draft.current_version
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
                'version': opinion_draft.current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

    def test_opinion_alert(self):
        """Test content alert"""

        text_publication = 'Aussi tôt dit, aussi tôt fait !'

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
                'version': opinion_draft.current_version
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        self.assertEqual(PublishedContent.objects.count(), 1)

        opinion = PublishableContent.objects.get(pk=opinion.pk)
        self.assertIsNotNone(opinion.public_version)
        self.assertEqual(opinion.public_version.sha_public, opinion_draft.current_version)

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
                'signal_text': 'Yeurk !'
            }, follow=False
        )

        self.assertEqual(result.status_code, 302)
        self.assertIsNotNone(Alert.objects.filter(author__pk=random_user.pk, content__pk=opinion.pk).first())

        alert = Alert.objects.filter(author__pk=random_user.pk, content__pk=opinion.pk).first()
        self.assertFalse(alert.solved)

        result = self.client.post(
            reverse('content:resolve-content', kwargs={'pk': opinion.pk}),
            {
                'alert_pk': alert.pk,
                'text': 'Je peux ?'
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
                'alert_pk': alert.pk,
                'text': 'Anéfé!'
            }, follow=False
        )
        self.assertEqual(result.status_code, 302)

        alert = Alert.objects.get(pk=alert.pk)
        self.assertTrue(alert.solved)
