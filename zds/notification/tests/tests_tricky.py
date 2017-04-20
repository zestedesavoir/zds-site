import os
import shutil

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from django.conf import settings
from zds.settings import BASE_DIR

from zds.forum.factories import CategoryFactory, ForumFactory
from zds.forum.models import Topic
from zds.gallery.factories import UserGalleryFactory
from zds.member.factories import StaffProfileFactory, ProfileFactory
from zds.notification.models import NewTopicSubscription, Notification, NewPublicationSubscription
from zds.notification import signals as notif_signals
from zds.tutorialv2.factories import PublishableContentFactory, LicenceFactory, SubCategoryFactory, \
    PublishedContentFactory
from zds.tutorialv2.publication_utils import publish_content


class ForumNotification(TestCase):
    def setUp(self):
        self.user1 = ProfileFactory().user
        self.user2 = ProfileFactory().user
        self.staff = StaffProfileFactory().user
        self.assertTrue(self.staff.has_perm('forum.change_topic'))
        self.category1 = CategoryFactory(position=1)
        self.forum11 = ForumFactory(category=self.category1, position_in_category=1)
        self.forum12 = ForumFactory(category=self.category1, position_in_category=2)
        for group in self.staff.groups.all():
            self.forum12.groups.add(group)
        self.forum12.save()

    def test_no_dead_notif_on_moving(self):
        NewTopicSubscription.objects.get_or_create_active(self.user1, self.forum11)
        self.assertTrue(self.client.login(username=self.user2.username, password='hostel77'))
        result = self.client.post(
            reverse('topic-new') + '?forum={0}'.format(self.forum11.pk),
            {
                'title': u'Super sujet',
                'subtitle': u'Pour tester les notifs',
                'text': u"En tout cas l'un abonnement",
                'tags': ''
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        topic = Topic.objects.filter(title=u'Super sujet').first()
        subscription = NewTopicSubscription.objects.get_existing(self.user1, self.forum11, True)
        self.assertIsNotNone(subscription, 'There must be an active subscription for now')
        self.assertIsNotNone(subscription.last_notification, 'There must be a notification for now')
        self.assertFalse(subscription.last_notification.is_read)
        self.client.logout()
        self.assertTrue(self.client.login(username=self.staff.username, password='hostel77'))
        data = {
            'move': '',
            'forum': self.forum12.pk,
            'topic': topic.pk
        }
        response = self.client.post(reverse('topic-edit'), data, follow=False)
        self.assertEqual(302, response.status_code)
        subscription = NewTopicSubscription.objects.get_existing(self.user1, self.forum11, True)
        self.assertIsNotNone(subscription, 'There must still be an active subscription')
        self.assertIsNotNone(subscription.last_notification,
                             'There must still be a notification as object is not removed.')
        self.assertEqual(subscription.last_notification,
                         Notification.objects.filter(sender=self.user2).first())
        self.assertTrue(subscription.last_notification.is_read, 'As forum is not reachable, notification is read')


overrided_zds_app = settings.ZDS_APP
overrided_zds_app['content']['repo_private_path'] = os.path.join(BASE_DIR, 'contents-private-test')
overrided_zds_app['content']['repo_public_path'] = os.path.join(BASE_DIR, 'contents-public-test')
overrided_zds_app['content']['extra_content_generation_policy'] = 'SYNC'


@override_settings(MEDIA_ROOT=os.path.join(BASE_DIR, 'media-test'))
@override_settings(ZDS_APP=overrided_zds_app)
@override_settings(ES_ENABLED=False)
class ContentNotification(TestCase):
    def setUp(self):

        # don't build PDF to speed up the tests
        settings.ZDS_APP['content']['build_pdf_when_published'] = False

        self.user1 = ProfileFactory().user
        self.user2 = ProfileFactory().user

        # create a tutorial
        self.tuto = PublishableContentFactory(type='TUTORIAL')
        self.tuto.authors.add(self.user1)
        UserGalleryFactory(gallery=self.tuto.gallery, user=self.user1, mode='W')
        self.tuto.licence = LicenceFactory()
        self.tuto.subcategory.add(SubCategoryFactory())
        self.tuto.save()
        tuto_draft = self.tuto.load_version()

        # then, publish it !
        version = tuto_draft.current_version
        self.published = publish_content(self.tuto, tuto_draft, is_major_update=True)

        self.tuto.sha_public = version
        self.tuto.sha_draft = version
        self.tuto.public_version = self.published
        self.tuto.save()

        self.assertTrue(self.client.login(username=self.user1.username, password='hostel77'))

    def test_no_persistant_notif_on_revoke(self):
        from zds.tutorialv2.publication_utils import unpublish_content
        NewPublicationSubscription.objects.get_or_create_active(self.user1, self.user2)
        content = PublishedContentFactory(author_list=[self.user2])

        notif_signals.new_content.send(sender=self.tuto.__class__, instance=content, by_email=False)
        self.assertEqual(1, len(Notification.objects.get_notifications_of(self.user1)))
        unpublish_content(content)
        self.assertEqual(0, len(Notification.objects.get_notifications_of(self.user1)))

    def tearDown(self):

        if os.path.isdir(settings.ZDS_APP['content']['repo_private_path']):
            shutil.rmtree(settings.ZDS_APP['content']['repo_private_path'])
        if os.path.isdir(settings.ZDS_APP['content']['repo_public_path']):
            shutil.rmtree(settings.ZDS_APP['content']['repo_public_path'])
        if os.path.isdir(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)

        # re-active PDF build
        settings.ZDS_APP['content']['build_pdf_when_published'] = True
