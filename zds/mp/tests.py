# coding: utf-8

from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase

from zds import settings
from zds.member.factories import ProfileFactory, StaffProfileFactory
from zds.mp.factories import PrivateTopicFactory, PrivatePostFactory
from zds.mp.models import PrivateTopic, PrivatePost
from zds.utils import slugify


class MPTests(TestCase):

    def setUp(self):
        self.user1 = ProfileFactory().user
        self.staff = StaffProfileFactory().user
        log = self.client.login(
            username=self.user1.username,
            password='hostel77')
        self.assertEqual(log, True)

        settings.EMAIL_BACKEND = \
            'django.core.mail.backends.locmem.EmailBackend'

    def test_mp_from_profile(self):
        """Test: Send a MP from a user profile."""
        # User to send the MP
        user2 = ProfileFactory().user

        # Test if user is correctly added to the MP
        result = self.client.get(
            reverse('zds.mp.views.new') +
            '?username={0}'.format(
                user2.username),
        )

        # Check username in new MP page
        self.assertContains(result, user2.username)

    def test_view_mp(self):
        """check mp is readable."""
        ptopic1 = PrivateTopicFactory(author=self.user1)
        PrivatePostFactory(
            privatetopic=ptopic1,
            author=self.user1,
            position_in_topic=1)
        PrivatePostFactory(
            privatetopic=ptopic1,
            author=self.staff,
            position_in_topic=2)
        PrivatePostFactory(
            privatetopic=ptopic1,
            author=self.user1,
            position_in_topic=3)

        result = self.client.get(
            reverse(
                'zds.mp.views.topic',
                args=[
                    ptopic1.pk,
                    slugify(ptopic1.title)]),
            follow=True)
        self.assertEqual(result.status_code, 200)

    def test_create_mp(self):
        """To test all aspects of mp's creation by member."""
        # Another User
        user2 = ProfileFactory().user
        user3 = ProfileFactory().user

        result = self.client.post(
            reverse('zds.mp.views.new'),
            {
                'participants': '{0}, {1}'.format(user2.username,
                                                  user3.username),
                'title': u'Un autre MP',
                'subtitle': u'Encore ces lombards en plein été',
                'text': u'C\'est tout simplement l\'histoire de la ville de Paris que je voudrais vous conter '
            },
            follow=False)
        self.assertEqual(result.status_code, 302)

        # check topic's number
        self.assertEqual(PrivateTopic.objects.all().count(), 1)
        ptopic = PrivateTopic.objects.get(pk=1)
        # check post's number
        self.assertEqual(PrivatePost.objects.all().count(), 1)
        ppost = PrivatePost.objects.get(pk=1)

        # check topic and post
        self.assertEqual(ppost.privatetopic, ptopic)

        # check position
        self.assertEqual(ppost.position_in_topic, 1)

        self.assertEqual(ppost.author, self.user1)

        # check last message
        self.assertEqual(ptopic.last_message, ppost)

        # check email has been sent
        self.assertEquals(len(mail.outbox), 2)

        # check view authorisations
        user4 = ProfileFactory().user
        staff1 = StaffProfileFactory().user

        # user2 and user3 can view mp
        self.client.login(username=user2.username, password='hostel77')
        result = self.client.get(
            reverse(
                'zds.mp.views.topic',
                args=[
                    ptopic.pk,
                    ptopic.pk]),
            follow=True)
        self.assertEqual(result.status_code, 200)
        self.client.login(username=user3.username, password='hostel77')
        result = self.client.get(
            reverse(
                'zds.mp.views.topic',
                args=[
                    ptopic.pk,
                    ptopic.pk]),
            follow=True)
        self.assertEqual(result.status_code, 200)

        # user4 and staff1 can't view mp
        self.client.login(username=user4.username, password='hostel77')
        result = self.client.get(
            reverse(
                'zds.mp.views.topic',
                args=[
                    ptopic.pk,
                    ptopic.pk]),
            follow=True)
        self.assertNotEqual(result.status_code, 200)
        self.client.login(username=staff1.username, password='hostel77')
        result = self.client.get(
            reverse(
                'zds.mp.views.topic',
                args=[
                    ptopic.pk,
                    ptopic.pk]),
            follow=True)
        self.assertNotEqual(result.status_code, 200)

    def test_edit_mp_post(self):
        """To test all aspects of the edition of simple mp post by member."""

        ptopic1 = PrivateTopicFactory(author=self.user1)
        ppost1 = PrivatePostFactory(
            privatetopic=ptopic1,
            author=self.user1,
            position_in_topic=1)
        ppost2 = PrivatePostFactory(
            privatetopic=ptopic1,
            author=self.user1,
            position_in_topic=2)
        ppost3 = PrivatePostFactory(
            privatetopic=ptopic1,
            author=self.user1,
            position_in_topic=3)

        result = self.client.post(
            reverse('zds.mp.views.edit_post') + '?message={0}'
            .format(ppost3.pk),
            {
                'text': u'C\'est tout simplement l\'histoire de la ville de Paris que je voudrais vous conter '
            },
            follow=False)

        self.assertEqual(result.status_code, 302)

        # check topic's number
        self.assertEqual(PrivateTopic.objects.all().count(), 1)

        # check post's number
        self.assertEqual(PrivatePost.objects.all().count(), 3)

        # check topic and post
        self.assertEqual(ppost1.privatetopic, ptopic1)
        self.assertEqual(ppost2.privatetopic, ptopic1)
        self.assertEqual(ppost3.privatetopic, ptopic1)

        # check values
        self.assertEqual(
            PrivatePost.objects.get(
                pk=ppost3.pk).text,
            u"C\'est tout simplement l\'histoire de la ville de Paris que je voudrais vous conter ")

        # check no email has been sent
        self.assertEquals(len(mail.outbox), 0)

        # i can edit a mp if it's not last
        result = self.client.post(
            reverse('zds.mp.views.edit_post') + '?message={0}'
            .format(ppost2.pk),
            {
                'text': u"C\'est tout simplement l\'histoire de la ville de Paris que je voudrais vous conter "
            },
            follow=False)

        self.assertEqual(result.status_code, 403)

        # staff can't edit mp if he's not author
        staff = StaffProfileFactory().user
        log = self.client.login(username=staff.username, password='hostel77')
        self.assertEqual(log, True)

        result = self.client.post(
            reverse('zds.mp.views.edit_post') + '?message={0}'
            .format(ppost3.pk),
            {
                'text': u'C\'est tout simplement l\'histoire de la ville de Paris que je voudrais vous conter '
            },
            follow=False)

        self.assertEqual(result.status_code, 403)
