# coding: utf-8

import urllib

from django.test import TestCase
from django.core.urlresolvers import reverse

from zds.member.factories import ProfileFactory
from zds.mp.factories import PrivateTopicFactory, PrivatePostFactory
from zds.mp.models import PrivateTopic, PrivatePost
from zds.utils import slugify


class IndexViewTest(TestCase):

    def setUp(self):
        self.profile1 = ProfileFactory()
        self.profile2 = ProfileFactory()
        self.topic1 = PrivateTopicFactory(author=self.profile1.user)
        self.topic1.participants.add(self.profile2.user)
        self.post1 = PrivatePostFactory(
            privatetopic=self.topic1,
            author=self.profile1.user,
            position_in_topic=1)

        self.post2 = PrivatePostFactory(
            privatetopic=self.topic1,
            author=self.profile2.user,
            position_in_topic=2)

    def test_denies_anonymous(self):
        response = self.client.get(reverse('zds.mp.views.index'), follow=True)
        self.assertRedirects(
            response,
            reverse('zds.member.views.login_view')
            + '?next=' + urllib.quote(reverse('zds.mp.views.index'), ''))

    def test_success_delete_topic_no_participants(self):
        topic = PrivateTopicFactory(author=self.profile1.user)
        login_check = self.client.login(
            username=self.profile1.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)
        self.assertEqual(1, PrivateTopic.objects.filter(pk=topic.pk).count())

        response = self.client.post(
            reverse('zds.mp.views.index'),
            {
                'delete': '',
                'items': [topic.pk]
            }
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(0, PrivateTopic.objects.filter(pk=topic.pk).count())

    def test_success_delete_topic_as_author(self):

        login_check = self.client.login(
            username=self.profile1.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)

        response = self.client.post(
            reverse('zds.mp.views.index'),
            {
                'delete': '',
                'items': [self.topic1.pk]
            }
        )

        self.assertEqual(200, response.status_code)
        topic = PrivateTopic.objects.get(pk=self.topic1.pk)
        self.assertEqual(self.profile2.user, topic.author)
        self.assertNotIn(self.profile1.user, topic.participants.all())
        self.assertNotIn(self.profile2.user, topic.participants.all())

    def test_success_delete_topic_as_participant(self):

        login_check = self.client.login(
            username=self.profile2.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)

        response = self.client.post(
            reverse('zds.mp.views.index'),
            {
                'delete': '',
                'items': [self.topic1.pk]
            }
        )

        self.assertEqual(200, response.status_code)

        topic = PrivateTopic.objects.get(pk=self.topic1.pk)
        self.assertNotEqual(self.profile2.user, topic.author)
        self.assertNotIn(self.profile1.user, topic.participants.all())
        self.assertNotIn(self.profile2.user, topic.participants.all())

    def test_fail_delete_topic_not_belong_to_user(self):
        topic = PrivateTopicFactory(author=self.profile1.user)

        self.assertEqual(1, PrivateTopic.objects.filter(pk=topic.pk).count())

        login_check = self.client.login(
            username=self.profile2.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)

        self.client.post(
            reverse('zds.mp.views.index'),
            {
                'delete': '',
                'items': [topic.pk]
            }
        )

        self.assertEqual(1, PrivateTopic.objects.filter(pk=topic.pk).count())


class TopicViewTest(TestCase):

    def setUp(self):
        self.profile1 = ProfileFactory()
        self.profile2 = ProfileFactory()
        self.topic1 = PrivateTopicFactory(author=self.profile1.user)
        self.topic1.participants.add(self.profile2.user)
        self.post1 = PrivatePostFactory(
            privatetopic=self.topic1,
            author=self.profile1.user,
            position_in_topic=1)

        self.post2 = PrivatePostFactory(
            privatetopic=self.topic1,
            author=self.profile2.user,
            position_in_topic=2)

    def test_denies_anonymous(self):
        response = self.client.get(
            reverse(
                'zds.mp.views.topic',
                args=[self.topic1.pk, slugify(self.topic1.title)]),
            follow=True)
        self.assertRedirects(
            response,
            reverse('zds.member.views.login_view')
            + '?next=' + urllib.quote(reverse(
                'zds.mp.views.topic',
                args=[self.topic1.pk, slugify(self.topic1.title)]), ''))

    def test_fail_topic_no_exist(self):

        login_check = self.client.login(
            username=self.profile1.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)

        response = self.client.get(reverse(
            'zds.mp.views.topic',
            args=[12, 'test']))
        self.assertEqual(404, response.status_code)

    def test_fail_topic_no_permission(self):
        topic = PrivateTopicFactory(author=self.profile1.user)

        login_check = self.client.login(
            username=self.profile2.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)

        response = self.client.get(reverse(
            'zds.mp.views.topic',
            args=[topic.pk, 'test']),
            follow=True
        )

        self.assertEqual(403, response.status_code)

    def test_fail_topic_slug(self):
        login_check = self.client.login(
            username=self.profile1.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)

        response = self.client.get(reverse(
            'zds.mp.views.topic',
            args=[self.topic1.pk, 'test']),
            follow=True
        )

        self.assertRedirects(
            response,
            reverse(
                'zds.mp.views.topic',
                args=[self.topic1.pk, slugify(self.topic1.title)]),
        )


class NewTopicViewTest(TestCase):

    def setUp(self):
        self.profile1 = ProfileFactory()
        self.profile2 = ProfileFactory()

        login_check = self.client.login(
            username=self.profile1.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)

    def test_denies_anonymous(self):

        self.client.logout()
        response = self.client.get(reverse('zds.mp.views.new'), follow=True)

        self.assertRedirects(
            response,
            reverse('zds.member.views.login_view')
            + '?next=' + urllib.quote(reverse('zds.mp.views.new'), ''))

    def test_success_get_with_and_without_username(self):

        response = self.client.get(reverse('zds.mp.views.new'))

        self.assertEqual(200, response.status_code)
        self.assertIsNone(
            response.context['form'].initial['participants'])

        response2 = self.client.get(
            reverse('zds.mp.views.new')
            + '?username=' + self.profile2.user.username)

        self.assertEqual(200, response2.status_code)
        self.assertEqual(
            self.profile2.user.username,
            response2.context['form'].initial['participants'])

    def test_fail_get_with_username_not_exist(self):

        response2 = self.client.get(
            reverse('zds.mp.views.new')
            + '?username=wrongusername')

        self.assertEqual(200, response2.status_code)
        self.assertIsNone(
            response2.context['form'].initial['participants'])

    def test_success_preview(self):

        self.assertEqual(0, PrivateTopic.objects.all().count())
        response = self.client.post(
            reverse('zds.mp.views.new'),
            {
                'preview': '',
                'participants': self.profile2.user.username,
                'title': 'title',
                'subtitle': 'subtitle',
                'text': 'text'
            }
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(0, PrivateTopic.objects.all().count())

    def test_fail_new_topic_user_no_exist(self):

        self.assertEqual(0, PrivateTopic.objects.all().count())
        response = self.client.post(
            reverse('zds.mp.views.new'),
            {
                'participants': 'wronguser',
                'title': 'title',
                'subtitle': 'subtitle',
                'text': 'text'
            }
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(0, PrivateTopic.objects.all().count())

    def test_success_new_topic(self):

        self.assertEqual(0, PrivateTopic.objects.all().count())
        response = self.client.post(
            reverse('zds.mp.views.new'),
            {
                'participants': self.profile2.user.username,
                'title': 'title',
                'subtitle': 'subtitle',
                'text': 'text'
            },
            follow=True
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, PrivateTopic.objects.all().count())

    def test_fail_new_topic_user_add_only_himself(self):

        self.assertEqual(0, PrivateTopic.objects.all().count())
        response = self.client.post(
            reverse('zds.mp.views.new'),
            {
                'participants': self.profile1.user.username,
                'title': 'title',
                'subtitle': 'subtitle',
                'text': 'text'
            },
            follow=True
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(0, PrivateTopic.objects.all().count())

    def test_fail_new_topic_user_add_himself_and_others(self):

        self.assertEqual(0, PrivateTopic.objects.all().count())

        participants = self.profile1.user.username\
            + ',' + self.profile2.user.username

        response = self.client.post(
            reverse('zds.mp.views.new'),
            {
                'participants': participants,
                'title': 'title',
                'subtitle': 'subtitle',
                'text': 'text'
            },
            follow=True
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, PrivateTopic.objects.all().count())
        self.assertNotIn(
            self.profile1.user,
            PrivateTopic.objects.all()[0].participants.all()
        )


class EditViewTest(TestCase):

    def setUp(self):
        self.profile1 = ProfileFactory()
        self.profile2 = ProfileFactory()
        self.profile3 = ProfileFactory()

        self.topic1 = PrivateTopicFactory(author=self.profile1.user)
        self.topic1.participants.add(self.profile2.user)
        self.post1 = PrivatePostFactory(
            privatetopic=self.topic1,
            author=self.profile1.user,
            position_in_topic=1)

        self.post2 = PrivatePostFactory(
            privatetopic=self.topic1,
            author=self.profile2.user,
            position_in_topic=2)

        login_check = self.client.login(
            username=self.profile1.user.username,
            password='hostel77'
        )
        self.assertTrue(login_check)

    def test_denies_anonymous(self):

        self.client.logout()
        response = self.client.get(reverse('zds.mp.views.edit'), follow=True)

        self.assertRedirects(
            response,
            reverse('zds.member.views.login_view')
            + '?next=' + urllib.quote(reverse('zds.mp.views.edit'), ''))

    def test_fail_edit_topic_not_sending_topic_pk(self):

        response = self.client.post(reverse('zds.mp.views.edit'))

        self.assertEqual(404, response.status_code)

    def test_fail_edit_topic_no_exist(self):

        response = self.client.post(
            reverse('zds.mp.views.edit'),
            {
                'privatetopic': 156
            }
        )

        self.assertEqual(404, response.status_code)

    def test_fail_edit_topic_add_no_exist_user(self):

        response = self.client.post(
            reverse('zds.mp.views.edit'),
            {
                'privatetopic': self.topic1.pk,
                'username': 'wrongusername'
            }
        )

        self.assertEqual(404, response.status_code)

    def test_success_edit_topic_add_participant(self):

        response = self.client.post(
            reverse('zds.mp.views.edit'),
            {
                'privatetopic': self.topic1.pk,
                'username': self.profile3.user.username
            },
            follow=True
        )

        self.assertEqual(200, response.status_code)
        topic = PrivateTopic.objects.get(pk=self.topic1.pk)
        self.assertIn(
            self.profile3.user,
            topic.participants.all()
        )

    def test_fail_user_add_himself_to_private_topic_with_no_right(self):

        self.client.logout()
        self.assertTrue(
            self.client.login(
                username=self.profile3.user.username,
                password='hostel77'
            )
        )

        self.client.post(
            reverse('zds.mp.views.edit'),
            {
                'privatetopic': self.topic1.pk,
                'username': self.profile3.user.username
            },
            follow=True
        )

        # self.assertEqual(403, response.status_code)
        topic = PrivateTopic.objects.get(pk=self.topic1.pk)
        self.assertNotIn(
            self.profile3.user,
            topic.participants.all()
        )


class AnswerViewTest(TestCase):

    def setUp(self):
        self.profile1 = ProfileFactory()
        self.profile2 = ProfileFactory()
        self.profile3 = ProfileFactory()

        self.topic1 = PrivateTopicFactory(author=self.profile1.user)
        self.topic1.participants.add(self.profile2.user)
        self.post1 = PrivatePostFactory(
            privatetopic=self.topic1,
            author=self.profile1.user,
            position_in_topic=1)

        self.post2 = PrivatePostFactory(
            privatetopic=self.topic1,
            author=self.profile2.user,
            position_in_topic=2)

        self.assertTrue(
            self.client.login(
                username=self.profile1.user.username,
                password='hostel77'
            )
        )

    def test_denies_anonymous(self):

        self.client.logout()
        response = self.client.get(reverse('zds.mp.views.answer'), follow=True)

        self.assertRedirects(
            response,
            reverse('zds.member.views.login_view')
            + '?next=' + urllib.quote(reverse('zds.mp.views.answer'), ''))

    def test_fail_answer_not_send_topic_pk(self):

        response = self.client.post(
            reverse('zds.mp.views.answer'),
            {}
        )

        self.assertEqual(404, response.status_code)

    def test_fail_answer_topic_no_exist(self):

        response = self.client.post(
            reverse('zds.mp.views.answer') + '?sujet=156',
            {}
        )

        self.assertEqual(404, response.status_code)

    def test_fail_cite_post_no_exist(self):

        response = self.client.get(
            reverse('zds.mp.views.answer')
            + '?sujet='+str(self.topic1.pk)
            + '&cite=4864',
            {}
        )

        self.assertEqual(404, response.status_code)

    def test_success_cite_post(self):

        response = self.client.get(
            reverse('zds.mp.views.answer')
            + '?sujet='+str(self.topic1.pk)
            + '&cite='+str(self.post1.pk),
            {}
        )

        self.assertEqual(200, response.status_code)

    def test_success_preview_answer(self):

        response = self.client.post(
            reverse('zds.mp.views.answer')
            + '?sujet='+str(self.topic1.pk),
            {
                'text': 'answer',
                'preview': '',
                'last_post': self.topic1.get_last_answer().pk
            },
            follow=True
        )

        self.assertEqual(200, response.status_code)

    def test_success_answer(self):

        response = self.client.post(
            reverse('zds.mp.views.answer')
            + '?sujet='+str(self.topic1.pk),
            {
                'text': 'answer',
                'last_post': self.topic1.get_last_answer().pk
            },
            follow=True
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(3, PrivatePost.objects.all().count())

    # TODO test mail notification

    def test_fail_answer_with_no_right(self):

        self.client.logout()
        self.assertTrue(
            self.client.login(
                username=self.profile3.user.username,
                password='hostel77'
            )
        )

        response = self.client.post(
            reverse('zds.mp.views.answer')
            + '?sujet='+str(self.topic1.pk),
            {
                'text': 'answer',
                'last_post': self.topic1.get_last_answer().pk
            },
            follow=True
        )

        self.assertEqual(403, response.status_code)
        self.assertEqual(2, PrivatePost.objects.all().count())


class EditPostViewTest(TestCase):

    def setUp(self):
        self.profile1 = ProfileFactory()
        self.profile2 = ProfileFactory()

        self.topic1 = PrivateTopicFactory(author=self.profile1.user)
        self.topic1.participants.add(self.profile2.user)
        self.post1 = PrivatePostFactory(
            privatetopic=self.topic1,
            author=self.profile1.user,
            position_in_topic=1)

        self.post2 = PrivatePostFactory(
            privatetopic=self.topic1,
            author=self.profile2.user,
            position_in_topic=2)

        self.assertTrue(
            self.client.login(
                username=self.profile1.user.username,
                password='hostel77'
            )
        )

    def test_denies_anonymous(self):

        self.client.logout()
        response = self.client.get(reverse('zds.mp.views.edit_post'), follow=True)

        self.assertRedirects(
            response,
            reverse('zds.member.views.login_view')
            + '?next=' + urllib.quote(reverse('zds.mp.views.edit_post'), ''))

    def test_succes_get_edit_post_page(self):

        self.client.logout()
        self.assertTrue(
            self.client.login(
                username=self.profile2.user.username,
                password='hostel77'
            )
        )

        response = self.client.get(
            reverse('zds.mp.views.edit_post')
            + '?message='+str(self.post2.pk)
        )

        self.assertEqual(200, response.status_code)

    def test_fail_edit_post_no_exist(self):

        response = self.client.get(
            reverse('zds.mp.views.edit_post')
            + '?message=154'
        )

        self.assertEqual(404, response.status_code)

    def test_fail_edit_post_not_last(self):

        response = self.client.get(
            reverse('zds.mp.views.edit_post')
            + '?message='+str(self.post1.pk)
        )

        self.assertEqual(403, response.status_code)

    def test_fail_edit_post_with_no_right(self):

        response = self.client.get(
            reverse('zds.mp.views.edit_post')
            + '?message='+str(self.post2.pk)
        )

        self.assertEqual(403, response.status_code)

    def test_success_edit_post_preview(self):

        self.client.logout()
        self.assertTrue(
            self.client.login(
                username=self.profile2.user.username,
                password='hostel77'
            )
        )

        response = self.client.post(
            reverse('zds.mp.views.edit_post')
            + '?message='+str(self.post2.pk),
            {
                'text': 'update post',
                'preview': ''
            }
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(
            'update post',
            response.context['form'].initial['text']
        )

    def test_success_edit_post(self):

        self.client.logout()
        self.assertTrue(
            self.client.login(
                username=self.profile2.user.username,
                password='hostel77'
            )
        )

        response = self.client.post(
            reverse('zds.mp.views.edit_post')
            + '?message='+str(self.post2.pk),
            {
                'text': 'update post',
            },
            follow=True
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(
            'update post',
            PrivatePost.objects.get(pk=self.post2.pk).text
        )


class LeaveViewTest(TestCase):

    def setUp(self):
        self.profile1 = ProfileFactory()
        self.profile2 = ProfileFactory()

        self.topic1 = PrivateTopicFactory(author=self.profile1.user)
        self.topic1.participants.add(self.profile2.user)
        self.post1 = PrivatePostFactory(
            privatetopic=self.topic1,
            author=self.profile1.user,
            position_in_topic=1)

        self.post2 = PrivatePostFactory(
            privatetopic=self.topic1,
            author=self.profile2.user,
            position_in_topic=2)

        self.assertTrue(
            self.client.login(
                username=self.profile1.user.username,
                password='hostel77'
            )
        )

    def test_denies_anonymous(self):

        self.client.logout()
        response = self.client.get(reverse('zds.mp.views.leave'), follow=True)

        self.assertRedirects(
            response,
            reverse('zds.member.views.login_view')
            + '?next=' + urllib.quote(reverse('zds.mp.views.leave'), ''))

    def test_fail_leave_topic_no_exist(self):

        response = self.client.post(
            reverse('zds.mp.views.leave'),
            {
                'leave': '',
                'topic_pk': '154'
            }
        )

        self.assertEqual(404, response.status_code)

    def test_success_leave_topic_as_author_no_participants(self):

        self.topic1.participants.remove(self.profile2)
        self.topic1.save()

        response = self.client.post(
            reverse('zds.mp.views.leave'),
            {
                'leave': '',
                'topic_pk': self.topic1.pk
            },
            follow=True
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(
            0,
            PrivateTopic.objects.all().count()
        )

    def test_success_leave_topic_as_author(self):

        response = self.client.post(
            reverse('zds.mp.views.leave'),
            {
                'leave': '',
                'topic_pk': self.topic1.pk
            },
            follow=True
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(
            1,
            PrivateTopic.objects.all().count()
        )

        self.assertEqual(
            self.profile2.user,
            PrivateTopic.objects.get(pk=self.topic1.pk).author
        )

    def test_success_leave_topic_as_participant(self):

        self.client.logout()
        self.assertTrue(
            self.client.login(
                username=self.profile2.user.username,
                password='hostel77'
            )
        )

        response = self.client.post(
            reverse('zds.mp.views.leave'),
            {
                'leave': '',
                'topic_pk': self.topic1.pk
            },
            follow=True
        )

        self.assertEqual(200, response.status_code)

        self.assertNotIn(
            self.profile2.user,
            PrivateTopic.objects.get(pk=self.topic1.pk).participants.all()
        )

        self.assertNotEqual(
            self.profile2.user,
            PrivateTopic.objects.get(pk=self.topic1.pk).author
        )


class AddParticipantViewTest(TestCase):

    def setUp(self):
        self.profile1 = ProfileFactory()
        self.profile2 = ProfileFactory()

        self.topic1 = PrivateTopicFactory(author=self.profile1.user)
        self.topic1.participants.add(self.profile2.user)
        self.post1 = PrivatePostFactory(
            privatetopic=self.topic1,
            author=self.profile1.user,
            position_in_topic=1)

        self.post2 = PrivatePostFactory(
            privatetopic=self.topic1,
            author=self.profile2.user,
            position_in_topic=2)

        self.assertTrue(
            self.client.login(
                username=self.profile1.user.username,
                password='hostel77'
            )
        )

    def test_denies_anonymous(self):

        self.client.logout()
        response = self.client.get(reverse('zds.mp.views.add_participant'), follow=True)

        self.assertRedirects(
            response,
            reverse('zds.member.views.login_view')
            + '?next=' + urllib.quote(reverse('zds.mp.views.add_participant'), ''))

    def test_fail_add_participant_topic_no_exist(self):

        response = self.client.post(
            reverse('zds.mp.views.add_participant'),
            {
                'topic_pk': '451'
            },
            follow=True
        )

        self.assertEqual(404, response.status_code)

    def test_fail_add_participant_who_no_exist(self):

        response = self.client.post(
            reverse('zds.mp.views.add_participant'),
            {
                'topic_pk': self.topic1.pk,
                'user_pk': '178548'
            },
            follow=True
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.context['messages']))

    def test_fail_add_participant_with_no_right(self):
        profile3 = ProfileFactory()

        self.client.logout()
        self.assertTrue(
            self.client.login(
                username=profile3.user.username,
                password='hostel77'
            )
        )

        response = self.client.post(
            reverse('zds.mp.views.add_participant'),
            {
                'topic_pk': self.topic1.pk,
                'user_pk': profile3.user.username
            }
        )

        self.assertEqual(403, response.status_code)
        self.assertNotIn(
            profile3.user,
            PrivateTopic.objects.get(pk=self.topic1.pk).participants.all()
        )

    def test_fail_add_participant_already_in(self):

        response = self.client.post(
            reverse('zds.mp.views.add_participant'),
            {
                'topic_pk': self.topic1.pk,
                'user_pk': self.profile2.user.username
            },
            follow=True
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.context['messages']))

    def test_success_add_participant(self):

        profile3 = ProfileFactory()

        response = self.client.post(
            reverse('zds.mp.views.add_participant'),
            {
                'topic_pk': self.topic1.pk,
                'user_pk': profile3.user.username
            },
            follow=True
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.context['messages']))
        self.assertIn(
            profile3.user,
            PrivateTopic.objects.get(pk=self.topic1.pk).participants.all()
        )
