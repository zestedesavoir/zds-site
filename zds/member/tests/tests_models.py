# coding: utf-8

import os
import shutil

from datetime import datetime

from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings
from hashlib import md5

from zds.article.factories import ArticleFactory
from zds.forum.factories import CategoryFactory, ForumFactory, TopicFactory, PostFactory
from zds.forum.models import TopicFollowed
from zds.member.factories import ProfileFactory, StaffProfileFactory
from zds.member.models import TokenForgotPassword, TokenRegister
from zds.tutorial.factories import MiniTutorialFactory
from zds.gallery.factories import GalleryFactory
from zds.utils.models import Alert
from zds.settings import SITE_ROOT


@override_settings(MEDIA_ROOT=os.path.join(SITE_ROOT, 'media-test'))
@override_settings(REPO_PATH=os.path.join(SITE_ROOT, 'tutoriels-private-test'))
@override_settings(REPO_PATH_PROD=os.path.join(SITE_ROOT, 'tutoriels-public-test'))
@override_settings(REPO_ARTICLE_PATH=os.path.join(SITE_ROOT, 'articles-data-test'))
class TestProfile(TestCase):

    def setUp(self):
        self.user1 = ProfileFactory()
        self.staff = StaffProfileFactory()

        # Create a forum for later test
        self.forumcat = CategoryFactory()
        self.forum = ForumFactory(category=self.forumcat)
        self.forumtopic = TopicFactory(forum=self.forum, author=self.staff.user)

    def test_unicode(self):
        self.assertEqual(self.user1.__unicode__(), self.user1.user.username)

    def test_get_absolute_url(self):
        self.assertEqual(self.user1.get_absolute_url(), '/membres/voir/{0}/'.format(self.user1.user.username))

    # def test_get_city(self):

    def test_get_avatar_url(self):
        # if no url was specified -> gravatar !
        self.assertEqual(self.user1.get_avatar_url(),
                         'https://secure.gravatar.com/avatar/{0}?d=identicon'.
                         format(md5(self.user1.user.email.lower()).hexdigest()))
        # if an url is specified -> take it !
        user2 = ProfileFactory()
        testurl = 'http://test.com/avatar.jpg'
        user2.avatar_url = testurl
        self.assertEqual(user2.get_avatar_url(), testurl)

    def test_get_post_count(self):
        # Start with 0
        self.assertEqual(self.user1.get_post_count(), 0)
        # Post !
        PostFactory(topic=self.forumtopic, author=self.user1.user, position=1)
        # Should be 1
        self.assertEqual(self.user1.get_post_count(), 1)

    def test_get_topic_count(self):
        # Start with 0
        self.assertEqual(self.user1.get_topic_count(), 0)
        # Create Topic !
        TopicFactory(forum=self.forum, author=self.user1.user)
        # Should be 1
        self.assertEqual(self.user1.get_topic_count(), 1)

    def test_get_tuto_count(self):
        # Start with 0
        self.assertEqual(self.user1.get_tuto_count(), 0)
        # Create Tuto !
        minituto = MiniTutorialFactory()
        minituto.authors.add(self.user1.user)
        minituto.gallery = GalleryFactory()
        minituto.save()
        # Should be 1
        self.assertEqual(self.user1.get_tuto_count(), 1)

    def test_get_tutos(self):
        # Start with 0
        self.assertEqual(len(self.user1.get_tutos()), 0)
        # Create Tuto !
        minituto = MiniTutorialFactory()
        minituto.authors.add(self.user1.user)
        minituto.gallery = GalleryFactory()
        minituto.save()
        # Should be 1
        tutos = self.user1.get_tutos()
        self.assertEqual(len(tutos), 1)
        self.assertEqual(minituto, tutos[0])

    def test_get_draft_tutos(self):
        # Start with 0
        self.assertEqual(len(self.user1.get_draft_tutos()), 0)
        # Create Tuto !
        drafttuto = MiniTutorialFactory()
        drafttuto.authors.add(self.user1.user)
        drafttuto.gallery = GalleryFactory()
        drafttuto.save()
        # Should be 1
        drafttutos = self.user1.get_draft_tutos()
        self.assertEqual(len(drafttutos), 1)
        self.assertEqual(drafttuto, drafttutos[0])

    def test_get_public_tutos(self):
        # Start with 0
        self.assertEqual(len(self.user1.get_public_tutos()), 0)
        # Create Tuto !
        publictuto = MiniTutorialFactory()
        publictuto.authors.add(self.user1.user)
        publictuto.gallery = GalleryFactory()
        publictuto.sha_public = 'whatever'
        publictuto.save()
        # Should be 1
        publictutos = self.user1.get_public_tutos()
        self.assertEqual(len(publictutos), 1)
        self.assertEqual(publictuto, publictutos[0])

    def test_get_validate_tutos(self):
        # Start with 0
        self.assertEqual(len(self.user1.get_validate_tutos()), 0)
        # Create Tuto !
        validatetuto = MiniTutorialFactory()
        validatetuto.authors.add(self.user1.user)
        validatetuto.gallery = GalleryFactory()
        validatetuto.sha_validation = 'whatever'
        validatetuto.save()
        # Should be 1
        validatetutos = self.user1.get_validate_tutos()
        self.assertEqual(len(validatetutos), 1)
        self.assertEqual(validatetuto, validatetutos[0])

    def test_get_beta_tutos(self):
        # Start with 0
        self.assertEqual(len(self.user1.get_beta_tutos()), 0)
        # Create Tuto !
        betatetuto = MiniTutorialFactory()
        betatetuto.authors.add(self.user1.user)
        betatetuto.gallery = GalleryFactory()
        betatetuto.sha_beta = 'whatever'
        betatetuto.save()
        # Should be 1
        betatetutos = self.user1.get_beta_tutos()
        self.assertEqual(len(betatetutos), 1)
        self.assertEqual(betatetuto, betatetutos[0])

    def test_get_articles(self):
        # Start with 0
        self.assertEqual(len(self.user1.get_articles()), 0)
        # Create Tuto !
        article = ArticleFactory()
        article.authors.add(self.user1.user)
        article.save()
        # Should be 1
        articles = self.user1.get_articles()
        self.assertEqual(len(articles), 1)
        self.assertEqual(article, articles[0])

    def test_get_public_articles(self):
        # Start with 0
        self.assertEqual(len(self.user1.get_public_articles()), 0)
        # Create Tuto !
        article = ArticleFactory()
        article.authors.add(self.user1.user)
        article.sha_public = 'whatever'
        article.save()
        # Should be 1
        articles = self.user1.get_public_articles()
        self.assertEqual(len(articles), 1)
        self.assertEqual(article, articles[0])

    def test_get_validate_articles(self):
        # Start with 0
        self.assertEqual(len(self.user1.get_validate_articles()), 0)
        # Create Tuto !
        article = ArticleFactory()
        article.authors.add(self.user1.user)
        article.sha_validation = 'whatever'
        article.save()
        # Should be 1
        articles = self.user1.get_validate_articles()
        self.assertEqual(len(articles), 1)
        self.assertEqual(article, articles[0])

    def test_get_draft_articles(self):
        # Start with 0
        self.assertEqual(len(self.user1.get_draft_articles()), 0)
        # Create Tuto !
        article = ArticleFactory()
        article.authors.add(self.user1.user)
        article.sha_beta = 'whatever'
        article.save()
        # Should be 1
        articles = self.user1.get_draft_articles()
        self.assertEqual(len(articles), 1)
        self.assertEqual(article, articles[0])

    def test_get_posts(self):
        # Start with 0
        self.assertEqual(len(self.user1.get_posts()), 0)
        # Post !
        apost = PostFactory(topic=self.forumtopic, author=self.user1.user, position=1)
        # Should be 1
        posts = self.user1.get_posts()
        self.assertEqual(len(posts), 1)
        self.assertEqual(apost, posts[0])

    def test_get_invisible_posts_count(self):
        # Start with 0
        self.assertEqual(self.user1.get_invisible_posts_count(), 0)
        # Post !
        PostFactory(topic=self.forumtopic, author=self.user1.user, position=1, is_visible=False)
        # Should be 1
        self.assertEqual(self.user1.get_invisible_posts_count(), 1)

    def test_get_alerts_posts_count(self):
        # Start with 0
        self.assertEqual(self.user1.get_alerts_posts_count(), 0)
        # Post and Alert it !
        post = PostFactory(topic=self.forumtopic, author=self.user1.user, position=1)
        Alert.objects.create(author=self.user1.user, comment=post, scope=Alert.FORUM, pubdate=datetime.now())
        # Should be 1
        self.assertEqual(self.user1.get_alerts_posts_count(), 1)

    def test_can_read_now(self):
        self.user1.user.is_active = False
        self.assertFalse(self.user1.can_write_now())
        self.user1.user.is_active = True
        self.assertTrue(self.user1.can_write_now())
        # TODO Some conditions still need to be tested

    def test_can_write_now(self):
        self.user1.user.is_active = False
        self.assertFalse(self.user1.can_write_now())
        self.user1.user.is_active = True
        self.assertTrue(self.user1.can_write_now())
        # TODO Some conditions still need to be tested

    def test_get_followed_topics(self):
        # Start with 0
        self.assertEqual(len(self.user1.get_followed_topics()), 0)
        # Follow !
        TopicFollowed.objects.create(topic=self.forumtopic, user=self.user1.user)
        # Should be 1
        topicsfollowed = self.user1.get_followed_topics()
        self.assertEqual(len(topicsfollowed), 1)
        self.assertEqual(self.forumtopic, topicsfollowed[0])

    def tearDown(self):
        if os.path.isdir(settings.ZDS_APP['tutorial']['repo_path']):
            shutil.rmtree(settings.ZDS_APP['tutorial']['repo_path'])
        if os.path.isdir(settings.ZDS_APP['tutorial']['repo_public_path']):
            shutil.rmtree(settings.ZDS_APP['tutorial']['repo_public_path'])
        if os.path.isdir(settings.ZDS_APP['article']['repo_path']):
            shutil.rmtree(settings.ZDS_APP['article']['repo_path'])
        if os.path.isdir(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)


class TestTokenForgotPassword(TestCase):

    def setUp(self):
        self.user1 = ProfileFactory()
        self.token = TokenForgotPassword.objects.create(user=self.user1.user,
                                                        token="abcde",
                                                        date_end=datetime.now())

    def test_get_absolute_url(self):
        self.assertEqual(self.token.get_absolute_url(), '/membres/new_password/?token={0}'.format(self.token.token))


class TestTokenRegister(TestCase):

    def setUp(self):
        self.user1 = ProfileFactory()
        self.token = TokenRegister.objects.create(user=self.user1.user,
                                                  token="abcde",
                                                  date_end=datetime.now())

    def test_get_absolute_url(self):
        self.assertEqual(self.token.get_absolute_url(), '/membres/activation/?token={0}'.format(self.token.token))

    def test_unicode(self):
        self.assertEqual(self.token.__unicode__(), '{0} - {1}'.format(self.user1.user.username, self.token.date_end))


# class TestBan(TestCase):
# nothing to test !


# class TestDivers(TestCase):
    # logout_user
    # listing
    # get_info_old_tuto
