from datetime import datetime, timedelta

from django.core.urlresolvers import reverse
from django.template import Context, Template
from django.test import TestCase

from zds.forum.factories import CategoryFactory, ForumFactory, PostFactory, TopicFactory
from zds.tutorialv2.models.database import Validation
from zds.tutorialv2.factories import PublishableContentFactory, LicenceFactory, SubCategoryFactory
from zds.member.factories import ProfileFactory, StaffProfileFactory, StaffFactory
from zds.utils.models import Alert
from zds.utils.mps import send_message_mp, send_mp
from zds.utils.templatetags.interventions import alerts_list


class InterventionsTest(TestCase):
    """
    This test uses quite complicated paths to check number of notifications:
    1. Create private topics and do stuff with them
    2. User signs in
    3. Render the home page
    4. Check the number of unread private messages on home page source code
    This because a correct test of this function requires a complete context (or it behaves strangely)
    """

    def setUp(self):
        self.licence = LicenceFactory()
        self.subcategory = SubCategoryFactory()

        self.author = ProfileFactory()
        self.user = ProfileFactory()
        self.staff = StaffProfileFactory()

        self.tuto = PublishableContentFactory(type='TUTORIAL')
        self.tuto.authors.add(self.author.user)
        self.tuto.licence = self.licence
        self.tuto.subcategory.add(self.subcategory)
        self.tuto.save()

        self.validation = Validation(
            content=self.tuto,
            version=self.tuto.sha_draft,
            comment_authors='bla',
            date_proposition=datetime.now(),
        )
        self.validation.save()

        self.topic = send_mp(author=self.author.user, users=[], title='Title', text='Testing', subtitle='', leave=False)
        self.topic.participants.add(self.user.user)
        send_message_mp(self.user.user, self.topic, 'Testing')

        # humane_delta test
        periods = ((1, 0), (2, 1), (3, 7), (4, 30), (5, 360))
        cont = dict()
        cont['date_today'] = periods[0][0]
        cont['date_yesterday'] = periods[1][0]
        cont['date_last_week'] = periods[2][0]
        cont['date_last_month'] = periods[3][0]
        cont['date_last_year'] = periods[4][0]
        self.context = Context(cont)

    def test_interventions_privatetopics(self):

        self.assertTrue(
            self.client.login(
                username=self.author.user.username,
                password='hostel77'
            )
        )
        response = self.client.post(reverse('homepage'))
        self.assertEqual(200, response.status_code)
        self.assertContains(response, '<span class="notif-count">1</span>', html=True)

        self.client.logout()

        self.assertTrue(
            self.client.login(
                username=self.user.user.username,
                password='hostel77'
            )
        )
        response = self.client.post(reverse('homepage'))
        self.assertEqual(200, response.status_code)
        self.assertContains(response, '<span class="notif-count">1</span>', html=True)

    def test_interventions_privatetopics_author_leave(self):

        # profile1 (author) leave topic
        move = self.topic.participants.first()
        self.topic.author = move
        self.topic.participants.remove(move)
        self.topic.save()

        self.assertTrue(
            self.client.login(
                username=self.user.user.username,
                password='hostel77'
            )
        )
        response = self.client.post(reverse('homepage'))
        self.assertEqual(200, response.status_code)
        self.assertContains(response, '<span class="notif-count">1</span>', html=True)

    def test_interventions_waiting_contents(self):
        # Login as staff
        self.assertTrue(
            self.client.login(
                username=self.staff.user.username,
                password='hostel77'
            )
        )

        # check that the number of waiting tutorials is correct
        response = self.client.post(reverse('homepage'))
        self.assertEqual(200, response.status_code)
        self.assertContains(response, '(1)')

        # Mark the content as reserved
        self.validation.status = 'PENDING_V'
        self.validation.save()

        # and check that the count was removed
        response = self.client.post(reverse('homepage'))
        self.assertEqual(200, response.status_code)
        self.assertNotContains(response, '(1)')

    def test_interventions_humane_delta(self):
        tr = Template('{% load interventions %}'
                      '{{ date_today|humane_delta }}'
                      ).render(self.context)
        self.assertEqual('Aujourd&#39;hui', tr)

        tr = Template('{% load interventions %}'
                      '{{ date_yesterday|humane_delta }}'
                      ).render(self.context)
        self.assertEqual('Hier', tr)

        tr = Template('{% load interventions %}'
                      '{{ date_last_week|humane_delta }}'
                      ).render(self.context)
        self.assertEqual('Les 7 derniers jours', tr)

        tr = Template('{% load interventions %}'
                      '{{ date_last_month|humane_delta }}'
                      ).render(self.context)
        self.assertEqual('Les 30 derniers jours', tr)

        tr = Template('{% load interventions %}'
                      '{{ date_last_year|humane_delta }}'
                      ).render(self.context)
        self.assertEqual('Plus ancien', tr)


class AlertsTest(TestCase):
    """
    This class intends to test the templatetag 'alerts_list'
    """

    def setUp(self):
        self.staff = StaffFactory()
        self.dummy_author = ProfileFactory()

        self.category = CategoryFactory(position=1)
        self.forum = ForumFactory(category=self.category, position_in_category=1)
        self.topic = TopicFactory(forum=self.forum, author=self.dummy_author.user)
        self.post = PostFactory(topic=self.topic, author=self.dummy_author.user, position=1)

        self.alerts = []
        for i in range(20):
            alert = Alert(author=self.dummy_author.user,
                          comment=self.post,
                          scope='FORUM',
                          text='pouet-{}'.format(i),
                          pubdate=(datetime.now() + timedelta(minutes=i)))
            alert.save()
            self.alerts.append(alert)

    def test_tag(self):

        all_alerts = alerts_list(user=self.staff)
        self.assertEqual(20, all_alerts['nb_alerts'])
        self.assertEqual(10, len(all_alerts['alerts']))
        self.assertEqual(self.alerts[-1].text, all_alerts['alerts'][0]['text'])

        self.alerts[5].delete()
        all_alerts = alerts_list(user=self.staff)
        self.assertEqual(19, all_alerts['nb_alerts'])
        self.assertEqual(10, len(all_alerts['alerts']))
