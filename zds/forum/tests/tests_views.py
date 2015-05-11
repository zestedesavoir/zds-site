# -*- coding: utf-8 -*-
from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse
from django.test import TestCase
from zds.forum.factories import CategoryFactory, ForumFactory
from zds.member.factories import ProfileFactory


class ForumsListViewTests(TestCase):
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


def create_category(group=None):
    category = CategoryFactory(position=1)
    forum = ForumFactory(category=category, position_in_category=1)
    if group is not None:
        forum.group.add(group)
        forum.save()
    return category, forum
