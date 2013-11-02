# coding: utf-8

from django.test import TestCase
from django.contrib.auth.models import User

from django_dynamic_fixture import G

from lbp.member.models import Profile
from .models import Category, Forum, Topic, Post


class ForumTests(TestCase):

    # Current URL tests

    def test_index_url(self):
        '''
        Tests if the index URL of the forum application ('/forums/') is ok.
        '''
        resp = self.client.get('/forums/')
        self.assertEqual(resp.status_code, 200)

    def test_category_url(self):
        category = G(Category, id=42, title='Test category',
                     slug='test-category')

        resp = self.client.get(category.get_absolute_url())
        self.assertEqual(resp.status_code, 200)

    def test_forum_url(self):
        category = G(Category, id=42, title='Test category',
                     slug='test-category')
        forum = G(Forum, id=21, title='Test forum', slug='test-forum',
                  category=category)

        resp = self.client.get(forum.get_absolute_url())
        self.assertEqual(resp.status_code, 200)

    # Deprecated URL redirect tests

    def test_deprecated_category_url_redirect(self):
        category = G(Category, id=42, title='Test category',
                     slug='test-category')

        resp = self.client.get('/forums/42-test-category/')
        self.assertRedirects(resp, category.get_absolute_url(), 301)

    def test_deprecated_forum_url_redirect(self):
        category = G(Category, id=42, title='Test category',
                     slug='test-category')
        forum = G(Forum, id=21, title='Test forum', slug='test-forum',
                  category=category)

        resp = self.client.get('/forums/42-test-category/21-test-forum/')
        self.assertRedirects(resp, forum.get_absolute_url(), 301)

    def test_deprecated_topic_url_redirect(self):
        author = G(User, username='monique')
        author_profile = G(Profile, user=author)

        category = G(Category, id=42, title='Test category',
                     slug='test-category')
        forum = G(Forum, id=21, title='Test forum', slug='test-forum',
                  category=category)

        topic = G(Topic, id=112, title='Test topic', forum=forum,
                  author=author, last_message=G(Post, topic_id=112,
                                                author=author))

        resp = self.client.get('/forums/sujet/112-test-topic')
        self.assertRedirects(resp, topic.get_absolute_url(), 301)

    def test_deprecated_feeds_redirect_rss(self):
        resp = self.client.get('/forums/flux/rss/')
        self.assertRedirects(resp, '/forums/flux/messages/rss/', 301)

    def test_deprecated_feeds_redirect_atom(self):
        resp = self.client.get('/forums/flux/atom/')
        self.assertRedirects(resp, '/forums/flux/messages/atom/', 301)
