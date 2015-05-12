# -*- coding: utf-8 -*-
from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse
from django.test import TestCase
from zds.forum.factories import CategoryFactory, ForumFactory, PostFactory, TopicFactory
from zds.member.factories import ProfileFactory


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


def create_category(group=None):
    category = CategoryFactory(position=1)
    forum = ForumFactory(category=category, position_in_category=1)
    if group is not None:
        forum.group.add(group)
        forum.save()
    return category, forum


def add_topic_in_a_forum(forum, profile, is_sticky=False, is_solved=False):
    topic = TopicFactory(forum=forum, author=profile.user)
    topic.is_sticky = is_sticky
    topic.is_solved = is_solved
    topic.save()
    PostFactory(topic=topic, author=profile.user, position=1)
    return topic
