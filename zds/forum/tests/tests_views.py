# -*- coding: utf-8 -*-
from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse
from django.test import TestCase
from zds.forum.factories import CategoryFactory, ForumFactory, TopicFactory, PostFactory
from zds.member.factories import ProfileFactory


class ForumsListViewTests(TestCase):
    def test_success_list_all_forums(self):
        profile = ProfileFactory()
        category = CategoryFactory(position=1)
        forum = ForumFactory(category=category, position_in_category=1)
        topic = TopicFactory(forum=forum, author=profile.user)
        PostFactory(topic=topic, author=profile.user, position=1)

        response = self.client.get(reverse('forums-list'))

        self.assertEqual(200, response.status_code)
        current_category = response.context['categories'].get(pk=category.pk)
        self.assertEqual(category, current_category)
        self.assertEqual(forum, current_category.get_forums(profile.user)[0])

    def test_success_list_all_forums_with_private_forums(self):
        group = Group.objects.create(name="DummyGroup_1")

        profile = ProfileFactory()
        category = CategoryFactory(position=1)
        forum = ForumFactory(category=category, position_in_category=1)
        forum.group.add(group)
        forum.save()
        topic = TopicFactory(forum=forum, author=profile.user)
        PostFactory(topic=topic, author=profile.user, position=1)

        response = self.client.get(reverse('forums-list'))

        self.assertEqual(200, response.status_code)
        current_category = response.context['categories'].get(pk=category.pk)
        self.assertEqual(category, current_category)
        self.assertEqual(0, len(current_category.get_forums(profile.user)))

        profile.user.groups.add(group)
        profile.user.save()
        self.assertTrue(self.client.login(username=profile.user.username, password='hostel77'))

        response = self.client.get(reverse('forums-list'))

        self.assertEqual(200, response.status_code)
        current_category = response.context['categories'].get(pk=category.pk)
        self.assertEqual(category, current_category)
        self.assertEqual(forum, current_category.get_forums(profile.user)[0])
