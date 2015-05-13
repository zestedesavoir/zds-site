# -*- coding: utf-8 -*-

from datetime import datetime

from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse
from django.test import TestCase
from zds.forum.factories import CategoryFactory, ForumFactory, PostFactory, TopicFactory, TagFactory
from zds.forum.models import TopicFollowed, Topic, Post
from zds.member.factories import ProfileFactory, StaffProfileFactory


class CategoriesForumsListViewTests(TestCase):
    def test_success_list_all_forums(self):
        profile = ProfileFactory()
        category, forum = create_category()

        response = self.client.get(reverse('cats-forums-list'))

        self.assertEqual(200, response.status_code)
        current_category = response.context['categories'].get(pk=category.pk)
        self.assertEqual(category, current_category)
        self.assertEqual(forum, current_category.get_forums(profile.user)[0])

    def test_success_list_all_forums_with_private_forums(self):
        group = Group.objects.create(name="DummyGroup_1")

        profile = ProfileFactory()
        category, forum = create_category(group)

        response = self.client.get(reverse('cats-forums-list'))

        self.assertEqual(200, response.status_code)
        current_category = response.context['categories'].get(pk=category.pk)
        self.assertEqual(category, current_category)
        self.assertEqual(0, len(current_category.get_forums(profile.user)))

        profile.user.groups.add(group)
        profile.user.save()
        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))

        response = self.client.get(reverse('cats-forums-list'))

        self.assertEqual(200, response.status_code)
        current_category = response.context['categories'].get(pk=category.pk)
        self.assertEqual(category, current_category)
        self.assertEqual(forum, current_category.get_forums(profile.user)[0])


class CategoryForumsDetailViewTest(TestCase):
    def test_success_list_all_forums_of_a_category(self):
        profile = ProfileFactory()
        category, forum = create_category()

        response = self.client.get(reverse('cat-forums-list', args=[category.slug]))

        self.assertEqual(200, response.status_code)
        current_category = response.context['category']
        self.assertEqual(category, current_category)
        self.assertEqual(forum, current_category.get_forums(profile.user)[0])
        self.assertEqual(response.context['forums'][0], current_category.get_forums(profile.user)[0])

    def test_success_list_all_forums_of_a_category_with_private_forums(self):
        group = Group.objects.create(name="DummyGroup_1")

        profile = ProfileFactory()
        category, forum = create_category(group)

        response = self.client.get(reverse('cat-forums-list', args=[category.slug]))

        self.assertEqual(200, response.status_code)
        current_category = response.context['category']
        self.assertEqual(category, current_category)
        self.assertEqual(0, len(response.context['forums']))

        profile.user.groups.add(group)
        profile.user.save()
        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))

        response = self.client.get(reverse('cat-forums-list', args=[category.slug]))

        self.assertEqual(200, response.status_code)
        current_category = response.context['category']
        self.assertEqual(category, current_category)
        self.assertEqual(forum, current_category.get_forums(profile.user)[0])
        self.assertEqual(response.context['forums'][0], current_category.get_forums(profile.user)[0])


class ForumTopicsListViewTest(TestCase):
    def test_failure_list_all_topics_of_a_wrong_forum(self):
        response = self.client.get(reverse('forum-topics-list', args=['x', 'x']))

        self.assertEqual(404, response.status_code)

    def test_failure_list_all_topics_of_a_forum_we_cannot_read(self):
        group = Group.objects.create(name="DummyGroup_1")
        category, forum = create_category(group)

        response = self.client.get(reverse('forum-topics-list', args=[category.slug, forum.slug]))

        self.assertEqual(403, response.status_code)

    def test_success_list_all_topics_of_a_forum(self):
        profile = ProfileFactory()
        category, forum = create_category()
        topic = add_topic_in_a_forum(forum, profile)

        response = self.client.get(reverse('forum-topics-list', args=[category.slug, forum.slug]))

        self.assertEqual(200, response.status_code)
        self.assertEqual(forum, response.context['forum'])
        self.assertEqual(1, len(response.context['topics']))
        self.assertEqual(topic, response.context['topics'][0])
        self.assertEqual(0, len(response.context['sticky_topics']))

    def test_success_list_all_topics_of_a_forum_with_sticky_topics(self):
        profile = ProfileFactory()
        category, forum = create_category()
        topic = add_topic_in_a_forum(forum, profile)
        topic_sticky = add_topic_in_a_forum(forum, profile, is_sticky=True)

        response = self.client.get(reverse('forum-topics-list', args=[category.slug, forum.slug]))

        self.assertEqual(200, response.status_code)
        self.assertEqual(forum, response.context['forum'])
        self.assertEqual(1, len(response.context['topics']))
        self.assertEqual(topic, response.context['topics'][0])
        self.assertEqual(1, len(response.context['sticky_topics']))
        self.assertEqual(topic_sticky, response.context['sticky_topics'][0])

    def test_success_filter_list_all_topics_solved_of_a_forum(self):
        profile = ProfileFactory()
        category, forum = create_category()
        add_topic_in_a_forum(forum, profile)
        topic_solved = add_topic_in_a_forum(forum, profile, is_solved=True)

        response = self.client.get(reverse('forum-topics-list', args=[category.slug, forum.slug]) + '?filter=solve')

        self.assertEqual(200, response.status_code)
        self.assertEqual(forum, response.context['forum'])
        self.assertEqual(1, len(response.context['topics']))
        self.assertEqual(topic_solved, response.context['topics'][0])

    def test_success_filter_list_all_topics_unsolved_of_a_forum(self):
        profile = ProfileFactory()
        category, forum = create_category()
        topic_unsolved = add_topic_in_a_forum(forum, profile)
        add_topic_in_a_forum(forum, profile, is_solved=True)

        response = self.client.get(reverse('forum-topics-list', args=[category.slug, forum.slug]) + '?filter=unsolve')

        self.assertEqual(200, response.status_code)
        self.assertEqual(forum, response.context['forum'])
        self.assertEqual(1, len(response.context['topics']))
        self.assertEqual(topic_unsolved, response.context['topics'][0])

    def test_success_filter_list_all_topics_noanswer_of_a_forum(self):
        profile = ProfileFactory()
        category, forum = create_category()
        add_topic_in_a_forum(forum, profile)
        add_topic_in_a_forum(forum, profile, is_solved=True)

        response = self.client.get(reverse('forum-topics-list', args=[category.slug, forum.slug]) + '?filter=noanswer')

        self.assertEqual(200, response.status_code)
        self.assertEqual(forum, response.context['forum'])
        self.assertEqual(2, len(response.context['topics']))


class TopicPostsListViewTest(TestCase):
    def test_failure_list_all_posts_of_a_topic_of_a_forum_we_cannot_read(self):
        group = Group.objects.create(name="DummyGroup_1")
        profile = ProfileFactory()
        category, forum = create_category(group)
        topic = add_topic_in_a_forum(forum, profile)

        response = self.client.get(reverse('topic-posts-list', args=[topic.pk, topic.slug()]))

        self.assertEqual(403, response.status_code)

    def test_failure_list_all_posts_of_a_topic_with_wrong_slug(self):
        profile = ProfileFactory()
        category, forum = create_category()
        topic = add_topic_in_a_forum(forum, profile)

        response = self.client.get(reverse('topic-posts-list', args=[topic.pk, 'x']))

        self.assertEqual(302, response.status_code)

    def test_success_list_all_posts_of_a_topic(self):
        profile = ProfileFactory()
        category, forum = create_category()
        topic = add_topic_in_a_forum(forum, profile)

        response = self.client.get(reverse('topic-posts-list', args=[topic.pk, topic.slug()]))

        self.assertEqual(200, response.status_code)
        self.assertEqual(topic, response.context['topic'])
        self.assertEqual(1, len(response.context['posts']))
        self.assertEqual(topic.last_message, response.context['posts'][0])
        self.assertEqual(topic.last_message.pk, response.context['last_post_pk'])
        self.assertIsNotNone(response.context['form'])
        self.assertIsNotNone(response.context['form_move'])


class TopicNewTest(TestCase):
    def test_failure_create_topic_with_a_post_with_client_unauthenticated(self):
        category, forum = create_category()

        response = self.client.post(reverse('topic-new') + '?forum={}'.format(forum.pk))

        self.assertEqual(302, response.status_code)

    def test_failure_create_topic_with_a_post_with_sanctioned_user(self):
        profile = ProfileFactory()
        profile.can_read = False
        profile.can_write = False
        profile.save()
        category, forum = create_category()

        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))
        response = self.client.post(reverse('topic-new') + '?forum={}'.format(forum.pk))

        self.assertEqual(403, response.status_code)

    def test_failure_create_topics_with_a_post_in_a_forum_we_cannot_read(self):
        group = Group.objects.create(name="DummyGroup_1")
        profile = ProfileFactory()
        category, forum = create_category(group)

        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))
        response = self.client.post(reverse('topic-new') + '?forum={}'.format(forum.pk))

        self.assertEqual(403, response.status_code)

    def test_failure_create_topics_with_a_post_with_wrong_forum(self):
        profile = ProfileFactory()

        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))
        response = self.client.post(reverse('topic-new') + '?forum=x')

        self.assertEqual(404, response.status_code)

    def test_success_create_topic_with_a_post_in_get_method(self):
        profile = ProfileFactory()
        category, forum = create_category()

        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))
        response = self.client.get(reverse('topic-new') + '?forum={}'.format(forum.pk))

        self.assertEqual(200, response.status_code)
        self.assertEqual(forum, response.context['forum'])
        self.assertIsNotNone(response.context['form'])

    def test_success_create_topic_with_post_in_preview_in_ajax(self):
        profile = ProfileFactory()
        category, forum = create_category()

        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))
        data = {
            'preview': '',
            'text': 'A new post!'
        }
        response = self.client.post(
            reverse('topic-new') + '?forum={}'.format(forum.pk),
            data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            follow=False
        )

        self.assertEqual(200, response.status_code)

    def test_success_create_topic_with_post_in_preview(self):
        profile = ProfileFactory()
        category, forum = create_category()

        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))
        data = {
            'preview': '',
            'title': 'Title of the topic',
            'subtitle': 'Subtitle of the topic',
            'text': 'A new post!'
        }
        response = self.client.post(reverse('topic-new') + '?forum={}'.format(forum.pk), data, follow=False)

        self.assertEqual(200, response.status_code)

    def test_success_create_topic_with_post(self):
        profile = ProfileFactory()
        category, forum = create_category()

        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))
        data = {
            'title': 'Title of the topic',
            'subtitle': 'Subtitle of the topic',
            'text': 'A new post!'
        }
        response = self.client.post(reverse('topic-new') + '?forum={}'.format(forum.pk), data, follow=False)

        self.assertEqual(302, response.status_code)


class TopicEditTest(TestCase):
    def test_failure_edit_topic_with_client_unauthenticated(self):
        response = self.client.post(reverse('topic-edit'))

        self.assertEqual(302, response.status_code)

    def test_failure_edit_topic_with_sanctioned_user(self):
        profile = ProfileFactory()
        profile.can_read = False
        profile.can_write = False
        profile.save()

        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))
        response = self.client.post(reverse('topic-edit'))

        self.assertEqual(403, response.status_code)

    def test_failure_edit_topic_with_method_get(self):
        response = self.client.get(reverse('topic-edit'))

        self.assertEqual(405, response.status_code)

    def test_failure_edit_topic_with_wrong_topic_pk(self):
        profile = ProfileFactory()

        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))
        response = self.client.post(
            reverse('topic-edit'),
            {
                'topic': 'abc',
            }, follow=False)

        self.assertEqual(404, response.status_code)

    def test_failure_edit_topic_with_a_topic_not_found(self):
        profile = ProfileFactory()

        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))
        response = self.client.post(
            reverse('topic-edit'),
            {
                'topic': 99999,
            }, follow=False)

        self.assertEqual(404, response.status_code)

    def test_success_edit_topic_in_ajax(self):
        profile = ProfileFactory()
        category, forum = create_category()
        topic = add_topic_in_a_forum(forum, profile)

        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))
        data = {
            'topic': topic.pk
        }
        response = self.client.post(reverse('topic-edit'), data, HTTP_X_REQUESTED_WITH='XMLHttpRequest', follow=False)

        self.assertEqual(200, response.status_code)

    def test_success_edit_topic(self):
        profile = ProfileFactory()
        category, forum = create_category()
        topic = add_topic_in_a_forum(forum, profile)

        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))
        data = {
            'topic': topic.pk
        }
        response = self.client.post(reverse('topic-edit'), data, follow=False)

        self.assertEqual(302, response.status_code)

    def test_success_edit_topic_follow(self):
        profile = ProfileFactory()
        category, forum = create_category()
        topic = add_topic_in_a_forum(forum, profile)

        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))
        data = {
            'follow': '',
            'topic': topic.pk
        }
        response = self.client.post(reverse('topic-edit'), data, follow=False)

        self.assertEqual(302, response.status_code)
        self.assertIsNotNone(TopicFollowed.objects.get(topic=topic, user=profile.user))

        response = self.client.post(reverse('topic-edit'), data, follow=False)

        self.assertEqual(302, response.status_code)
        try:
            TopicFollowed.objects.get(topic=topic, user=profile.user)
            self.fail()
        except TopicFollowed.DoesNotExist:
            pass

    def test_success_edit_topic_follow_email(self):
        profile = ProfileFactory()
        category, forum = create_category()
        topic = add_topic_in_a_forum(forum, profile)

        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))
        data = {
            'email': '',
            'topic': topic.pk
        }
        response = self.client.post(reverse('topic-edit'), data, follow=False)

        self.assertEqual(302, response.status_code)
        self.assertIsNotNone(TopicFollowed.objects.get(topic=topic, user=profile.user, email=True))

        response = self.client.post(reverse('topic-edit'), data, follow=False)

        self.assertEqual(302, response.status_code)
        try:
            TopicFollowed.objects.get(topic=topic, user=profile.user, email=True)
            self.fail()
        except TopicFollowed.DoesNotExist:
            pass

    def test_failure_edit_topic_solved_not_author(self):
        profile = ProfileFactory()

        another_profile = ProfileFactory()
        category, forum = create_category()
        topic = add_topic_in_a_forum(forum, another_profile)

        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))
        data = {
            'solved': '',
            'topic': topic.pk
        }
        response = self.client.post(reverse('topic-edit'), data, follow=False)

        self.assertEqual(403, response.status_code)

    def test_success_edit_topic_solved_by_author(self):
        profile = ProfileFactory()
        category, forum = create_category()
        topic = add_topic_in_a_forum(forum, profile)

        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))
        data = {
            'solved': '',
            'topic': topic.pk
        }
        response = self.client.post(reverse('topic-edit'), data, follow=False)

        self.assertEqual(302, response.status_code)
        self.assertTrue(Topic.objects.get(pk=topic.pk).is_solved)

    def test_success_edit_topic_solved_by_staff(self):
        staff = StaffProfileFactory()

        profile = ProfileFactory()
        category, forum = create_category()
        topic = add_topic_in_a_forum(forum, profile)

        self.assertTrue(self.client.login(username=staff.user.username, password='hostel77'))
        data = {
            'solved': '',
            'topic': topic.pk
        }
        response = self.client.post(reverse('topic-edit'), data, follow=False)

        self.assertEqual(302, response.status_code)
        self.assertTrue(Topic.objects.get(pk=topic.pk).is_solved)

    def test_failure_edit_topic_lock_by_user(self):
        profile = ProfileFactory()

        another_profile = ProfileFactory()
        category, forum = create_category()
        topic = add_topic_in_a_forum(forum, another_profile)

        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))
        data = {
            'lock': 'true',
            'topic': topic.pk
        }
        response = self.client.post(reverse('topic-edit'), data, follow=False)

        self.assertEqual(403, response.status_code)

    def test_success_edit_topic_lock_by_staff(self):
        staff = StaffProfileFactory()

        profile = ProfileFactory()
        category, forum = create_category()
        topic = add_topic_in_a_forum(forum, profile)

        self.assertTrue(self.client.login(username=staff.user.username, password='hostel77'))
        data = {
            'lock': 'true',
            'topic': topic.pk
        }
        response = self.client.post(reverse('topic-edit'), data, follow=False)

        self.assertEqual(302, response.status_code)
        self.assertTrue(Topic.objects.get(pk=topic.pk).is_locked)

        data = {
            'lock': 'false',
            'topic': topic.pk
        }
        response = self.client.post(reverse('topic-edit'), data, follow=False)

        self.assertEqual(302, response.status_code)
        self.assertFalse(Topic.objects.get(pk=topic.pk).is_locked)

    def test_failure_edit_topic_sticky_by_user(self):
        profile = ProfileFactory()

        another_profile = ProfileFactory()
        category, forum = create_category()
        topic = add_topic_in_a_forum(forum, another_profile)

        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))
        data = {
            'sticky': 'true',
            'topic': topic.pk
        }
        response = self.client.post(reverse('topic-edit'), data, follow=False)

        self.assertEqual(403, response.status_code)

    def test_success_edit_topic_sticky_by_staff(self):
        staff = StaffProfileFactory()

        profile = ProfileFactory()
        category, forum = create_category()
        topic = add_topic_in_a_forum(forum, profile)

        self.assertTrue(self.client.login(username=staff.user.username, password='hostel77'))
        data = {
            'sticky': 'true',
            'topic': topic.pk
        }
        response = self.client.post(reverse('topic-edit'), data, follow=False)

        self.assertEqual(302, response.status_code)
        self.assertTrue(Topic.objects.get(pk=topic.pk).is_sticky)

        data = {
            'sticky': 'false',
            'topic': topic.pk
        }
        response = self.client.post(reverse('topic-edit'), data, follow=False)

        self.assertEqual(302, response.status_code)
        self.assertFalse(Topic.objects.get(pk=topic.pk).is_sticky)

    def test_failure_edit_topic_move_by_user(self):
        profile = ProfileFactory()

        another_profile = ProfileFactory()
        category, forum = create_category()
        topic = add_topic_in_a_forum(forum, another_profile)

        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))
        data = {
            'move': '',
            'topic': topic.pk
        }
        response = self.client.post(reverse('topic-edit'), data, follow=False)

        self.assertEqual(403, response.status_code)

    def test_failure_edit_topic_move_with_wrong_forum_pk_by_staff(self):
        staff = StaffProfileFactory()

        profile = ProfileFactory()
        category, forum = create_category()
        topic = add_topic_in_a_forum(forum, profile)

        self.assertTrue(self.client.login(username=staff.user.username, password='hostel77'))
        data = {
            'move': '',
            'forum': 'abc',
            'topic': topic.pk
        }
        response = self.client.post(reverse('topic-edit'), data, follow=False)

        self.assertEqual(404, response.status_code)

    def test_failure_edit_topic_move_with_a_forum_not_found_by_staff(self):
        staff = StaffProfileFactory()

        profile = ProfileFactory()
        category, forum = create_category()
        topic = add_topic_in_a_forum(forum, profile)

        self.assertTrue(self.client.login(username=staff.user.username, password='hostel77'))
        data = {
            'move': '',
            'forum': 99999,
            'topic': topic.pk
        }
        response = self.client.post(reverse('topic-edit'), data, follow=False)

        self.assertEqual(404, response.status_code)

    def test_success_edit_topic_move_by_staff(self):
        staff = StaffProfileFactory()

        profile = ProfileFactory()
        category, forum = create_category()
        topic = add_topic_in_a_forum(forum, profile)

        another_category, another_forum = create_category()

        self.assertTrue(self.client.login(username=staff.user.username, password='hostel77'))
        data = {
            'move': '',
            'forum': another_forum.pk,
            'topic': topic.pk
        }
        response = self.client.post(reverse('topic-edit'), data, follow=False)

        self.assertEqual(302, response.status_code)


class FindTopicTest(TestCase):
    def test_failure_find_topics_of_a_member_not_found(self):
        response = self.client.get(reverse('topic-find', args=[9999]), follow=False)

        self.assertEqual(404, response.status_code)

    def test_success_find_topics_of_a_member(self):
        profile = ProfileFactory()
        category, forum = create_category()
        topic = add_topic_in_a_forum(forum, profile)

        response = self.client.get(reverse('topic-find', args=[profile.user.pk]), follow=False)

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.context['topics']))
        self.assertEqual(topic, response.context['topics'][0])


class FindTopicByTagTest(TestCase):
    def test_failure_find_topics_of_a_tag_not_found(self):
        response = self.client.get(reverse('topic-tag-find', args=[9999, 'x']), follow=False)

        self.assertEqual(404, response.status_code)

    def test_success_find_topics_of_a_tag(self):
        profile = ProfileFactory()
        category, forum = create_category()
        topic = add_topic_in_a_forum(forum, profile)
        tag = TagFactory()
        topic.add_tags([tag.title])

        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))
        response = self.client.get(reverse('topic-tag-find', args=[tag.pk, tag.slug]), follow=False)

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.context['topics']))
        self.assertEqual(topic, response.context['topics'][0])
        self.assertEqual(tag, response.context['tag'])

    def test_success_find_topics_of_a_tag_solved(self):
        profile = ProfileFactory()
        category, forum = create_category()
        add_topic_in_a_forum(forum, profile)
        topic_solved = add_topic_in_a_forum(forum, profile, is_solved=True)
        tag = TagFactory()
        topic_solved.add_tags([tag.title])

        response = self.client.get(reverse('topic-tag-find', args=[tag.pk, tag.slug]) + '?filter=solve')

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.context['topics']))
        self.assertEqual(topic_solved, response.context['topics'][0])
        self.assertEqual(tag, response.context['tag'])

    def test_success_filter_find_topics_of_a_tag_unsolved(self):
        profile = ProfileFactory()
        category, forum = create_category()
        add_topic_in_a_forum(forum, profile, is_solved=True)
        topic_unsolved = add_topic_in_a_forum(forum, profile)
        tag = TagFactory()
        topic_unsolved.add_tags([tag.title])

        response = self.client.get(reverse('topic-tag-find', args=[tag.pk, tag.slug]) + '?filter=unsolve')

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.context['topics']))
        self.assertEqual(topic_unsolved, response.context['topics'][0])
        self.assertEqual(tag, response.context['tag'])

    def test_success_filter_find_topics_of_a_tag_noanswer(self):
        profile = ProfileFactory()
        category, forum = create_category()
        topic = add_topic_in_a_forum(forum, profile)
        another_topic = add_topic_in_a_forum(forum, profile, is_solved=True)
        tag = TagFactory()
        topic.add_tags([tag.title])
        another_topic.add_tags([tag.title])

        response = self.client.get(reverse('topic-tag-find', args=[tag.pk, tag.slug]) + '?filter=noanswer')

        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.context['topics']))
        self.assertEqual(tag, response.context['tag'])


class PostNewTest(TestCase):
    def test_failure_new_post_with_client_unauthenticated(self):
        response = self.client.post(reverse('post-new'))

        self.assertEqual(302, response.status_code)

    def test_failure_new_post_with_sanctioned_user(self):
        profile = ProfileFactory()
        profile.can_read = False
        profile.can_write = False
        profile.save()

        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))
        response = self.client.post(reverse('post-new'))

        self.assertEqual(403, response.status_code)

    def test_failure_new_post_with_wrong_topic_pk(self):
        profile = ProfileFactory()

        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))
        response = self.client.post(reverse('post-new') + '?sujet=abc', follow=False)

        self.assertEqual(404, response.status_code)

    def test_failure_edit_topic_with_a_topic_not_found(self):
        profile = ProfileFactory()

        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))
        response = self.client.post(reverse('post-new') + '?sujet=99999', follow=False)

        self.assertEqual(404, response.status_code)

    def test_failure_new_post_in_a_forum_we_cannot_read(self):
        profile = ProfileFactory()
        group = Group.objects.create(name="DummyGroup_1")
        category, forum = create_category(group)
        topic = add_topic_in_a_forum(forum, profile)

        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))
        response = self.client.get(reverse('post-new') + '?sujet={}'.format(topic.pk))

        self.assertEqual(403, response.status_code)

    def test_failure_new_post_on_a_locked_topic(self):
        profile = ProfileFactory()
        category, forum = create_category()
        topic = add_topic_in_a_forum(forum, profile, is_locked=True)

        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))
        response = self.client.get(reverse('post-new') + '?sujet={}'.format(topic.pk))

        self.assertEqual(403, response.status_code)

    def test_failure_new_post_stopped_by_anti_spam(self):
        profile = ProfileFactory()
        category, forum = create_category()
        topic = add_topic_in_a_forum(forum, profile)
        topic.last_message.pubdate = datetime.now()
        topic.last_message.save()

        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))
        response = self.client.get(reverse('post-new') + '?sujet={}'.format(topic.pk))

        self.assertEqual(403, response.status_code)

    def test_success_new_post_method_get(self):
        another_profile = ProfileFactory()
        category, forum = create_category()
        topic = add_topic_in_a_forum(forum, another_profile)

        profile = ProfileFactory()
        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))
        response = self.client.get(reverse('post-new') + '?sujet={}'.format(topic.pk), follow=False)

        self.assertEqual(200, response.status_code)
        self.assertEqual(topic, response.context['topic'])
        self.assertEqual(topic.last_message, response.context['posts'][0])
        self.assertEqual(topic.last_message.pk, response.context['last_post_pk'])
        self.assertIsNotNone(response.context['form'])

    def test_success_new_post_with_quote_in_ajax(self):
        another_profile = ProfileFactory()
        category, forum = create_category()
        topic = add_topic_in_a_forum(forum, another_profile)

        profile = ProfileFactory()
        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))
        response = self.client.get(
            reverse('post-new') + '?sujet={0}&cite={1}'.format(topic.pk, topic.last_message.pk),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            follow=False
        )

        self.assertEqual(200, response.status_code)

    def test_success_new_post_in_preview(self):
        another_profile = ProfileFactory()
        category, forum = create_category()
        topic = add_topic_in_a_forum(forum, another_profile)

        profile = ProfileFactory()
        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))
        data = {
            'preview': '',
            'text': 'A new post!',
            'last_post': topic.last_message.pk
        }
        response = self.client.post(reverse('post-new') + '?sujet={}'.format(topic.pk), data, follow=False)

        self.assertEqual(200, response.status_code)
        self.assertEqual(topic, response.context['topic'])
        self.assertEqual(topic.last_message, response.context['posts'][0])
        self.assertEqual(topic.last_message.pk, response.context['last_post_pk'])
        self.assertIsNotNone(response.context['form'])

    def test_success_new_post_in_preview_in_ajax(self):
        another_profile = ProfileFactory()
        category, forum = create_category()
        topic = add_topic_in_a_forum(forum, another_profile)

        profile = ProfileFactory()
        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))
        data = {
            'preview': '',
            'text': 'A new post!',
            'last_post': topic.last_message.pk
        }
        response = self.client.post(
            reverse('post-new') + '?sujet={}'.format(topic.pk),
            data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            follow=False
        )

        self.assertEqual(200, response.status_code)

    def test_success_new_post(self):
        another_profile = ProfileFactory()
        category, forum = create_category()
        topic = add_topic_in_a_forum(forum, another_profile)

        profile = ProfileFactory()
        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))
        data = {
            'text': 'A new post!',
            'last_post': topic.last_message.pk
        }
        response = self.client.post(reverse('post-new') + '?sujet={}'.format(topic.pk), data, follow=False)

        self.assertEqual(302, response.status_code)
        self.assertEqual(2, Post.objects.filter(topic__pk=topic.pk).count())


def create_category(group=None):
    category = CategoryFactory(position=1)
    forum = ForumFactory(category=category, position_in_category=1)
    if group is not None:
        forum.group.add(group)
        forum.save()
    return category, forum


def add_topic_in_a_forum(forum, profile, is_sticky=False, is_solved=False, is_locked=False):
    topic = TopicFactory(forum=forum, author=profile.user)
    topic.is_sticky = is_sticky
    topic.is_solved = is_solved
    topic.is_locked = is_locked
    topic.save()
    PostFactory(topic=topic, author=profile.user, position=1)
    return topic
