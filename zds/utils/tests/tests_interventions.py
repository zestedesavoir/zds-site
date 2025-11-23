from datetime import datetime

from django.template import Context, Template
from django.test import TestCase
from django.urls import reverse
from django.utils.html import escape

from zds.member.tests.factories import ProfileFactory, StaffProfileFactory
from zds.mp.utils import send_message_mp, send_mp
from zds.tutorialv2.models.database import Validation
from zds.tutorialv2.tests.factories import PublishableContentFactory
from zds.utils.tests.factories import LicenceFactory, SubCategoryFactory


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

        self.tuto = PublishableContentFactory(type="TUTORIAL")
        self.tuto.authors.add(self.author.user)
        self.tuto.licence = self.licence
        self.tuto.subcategory.add(self.subcategory)
        self.tuto.save()

        self.validation = Validation(
            content=self.tuto,
            version=self.tuto.sha_draft,
            comment_authors="bla",
            date_proposition=datetime.now(),
        )
        self.validation.save()

        self.topic = send_mp(author=self.author.user, users=[], title="Title", subtitle="", text="Testing", leave=False)
        self.topic.add_participant(self.user.user)
        send_message_mp(self.user.user, self.topic, "Testing")

        # humane_delta test
        periods = ((1, 0), (2, 1), (3, 7), (4, 30), (5, 360))
        cont = dict()
        cont["date_today"] = periods[0][0]
        cont["date_yesterday"] = periods[1][0]
        cont["date_last_week"] = periods[2][0]
        cont["date_last_month"] = periods[3][0]
        cont["date_last_year"] = periods[4][0]
        self.context = Context(cont)

    def test_interventions_privatetopics(self):
        self.client.force_login(self.author.user)
        response = self.client.post(reverse("homepage"))
        self.assertEqual(200, response.status_code)
        self.assertContains(response, '<span class="notif-count">1</span>', html=True)

        self.client.logout()

        self.client.force_login(self.user.user)
        response = self.client.post(reverse("homepage"))
        self.assertEqual(200, response.status_code)
        self.assertContains(response, '<span class="notif-count">1</span>', html=True)

    def test_interventions_privatetopics_author_leave(self):
        # profile1 (author) leave topic
        move = self.topic.participants.first()
        self.topic.author = move
        self.topic.participants.remove(move)
        self.topic.save()

        self.client.force_login(self.user.user)
        response = self.client.post(reverse("homepage"))
        self.assertEqual(200, response.status_code)
        self.assertContains(response, '<span class="notif-count">1</span>', html=True)

    def test_interventions_waiting_contents(self):
        # Login as staff
        self.client.force_login(self.staff.user)

        # check that the number of waiting tutorials is correct
        response = self.client.post(reverse("homepage"))
        self.assertEqual(200, response.status_code)
        self.assertContains(response, "(1 tutoriel)")

        # Mark the content as reserved
        self.validation.status = "PENDING_V"
        self.validation.save()

        # and check that the count was removed
        response = self.client.post(reverse("homepage"))
        self.assertEqual(200, response.status_code)
        self.assertNotContains(response, "(1 tutoriel)")

    def test_interventions_humane_delta(self):
        tr = Template("{% load interventions %}" "{{ date_today|humane_delta }}").render(self.context)
        self.assertEqual(escape("Aujourd'hui"), tr)

        tr = Template("{% load interventions %}" "{{ date_yesterday|humane_delta }}").render(self.context)
        self.assertEqual("Hier", tr)

        tr = Template("{% load interventions %}" "{{ date_last_week|humane_delta }}").render(self.context)
        self.assertEqual("Les 7 derniers jours", tr)

        tr = Template("{% load interventions %}" "{{ date_last_month|humane_delta }}").render(self.context)
        self.assertEqual("Les 30 derniers jours", tr)

        tr = Template("{% load interventions %}" "{{ date_last_year|humane_delta }}").render(self.context)
        self.assertEqual("Plus ancien", tr)
