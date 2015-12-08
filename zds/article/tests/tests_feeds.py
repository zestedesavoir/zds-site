# coding: utf-8

import os
import shutil

from django.conf import settings
from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings

from zds.article.factories import ArticleFactory, LicenceFactory
from zds.article.models import Validation, Article
from zds.article.feeds import LastArticlesFeedRSS, LastArticlesFeedATOM
from zds.member.factories import ProfileFactory, StaffProfileFactory
from zds.settings import BASE_DIR


overrided_zds_app = settings.ZDS_APP
overrided_zds_app['article']['repo_path'] = os.path.join(BASE_DIR, 'article-data-test')


@override_settings(MEDIA_ROOT=os.path.join(BASE_DIR, 'media-test'))
@override_settings(ZDS_APP=overrided_zds_app)
class LastArticlesFeedRSSTest(TestCase):

    def setUp(self):

        settings.EMAIL_BACKEND = \
            'django.core.mail.backends.locmem.EmailBackend'
        self.mas = ProfileFactory().user
        settings.ZDS_APP['member']['bot_account'] = self.mas.username

        self.user_author = ProfileFactory().user
        self.user = ProfileFactory().user
        self.staff = StaffProfileFactory().user

        self.licence = LicenceFactory()

        self.article = ArticleFactory()
        self.article.authors.add(self.user_author)
        self.article.licence = self.licence
        self.article.save()

        # connect with user
        login_check = self.client.login(
            username=self.user_author.username,
            password='hostel77')
        self.assertEqual(login_check, True)

        # ask public article
        pub = self.client.post(
            reverse('article-modify'),
            {
                'article': self.article.pk,
                'comment': u'Valides moi ce bébé',
                'pending': 'Demander validation',
                'version': self.article.sha_draft,
                'is_major': True
            },
            follow=False)
        self.assertEqual(pub.status_code, 302)
        self.assertEqual(Validation.objects.count(), 1)

        login_check = self.client.login(
            username=self.staff.username,
            password='hostel77')
        self.assertEqual(login_check, True)

        # reserve tutorial
        validation = Validation.objects.get(
            article__pk=self.article.pk)
        pub = self.client.post(
            reverse('article-reservation', args=[validation.pk]),
            follow=False)
        self.assertEqual(pub.status_code, 302)

        # publish article
        pub = self.client.post(
            reverse('article-modify'),
            {
                'article': self.article.pk,
                'comment-v': u'Cet article est excellent',
                'valid-article': 'Demander validation',
                'is_major': True
            },
            follow=False)
        self.assertEqual(pub.status_code, 302)
        self.assertEquals(len(mail.outbox), 1)
        mail.outbox = []

        self.articlefeed = LastArticlesFeedRSS()

    def test_is_well_setup(self):
        """ Test that base parameters are Ok """

        self.assertEqual(self.articlefeed.link, '/articles/')
        reftitle = u"Articles sur {}".format(settings.ZDS_APP['site']['litteral_name'])
        self.assertEqual(self.articlefeed.title, reftitle)
        refdescription = u"Les derniers articles parus sur {}.".format(settings.ZDS_APP['site']['litteral_name'])
        self.assertEqual(self.articlefeed.description, refdescription)

        atom = LastArticlesFeedATOM()
        self.assertEqual(atom.subtitle, refdescription)

    def test_get_items(self):
        """ basic test sending back the article """

        ret = self.articlefeed.items()
        self.assertEqual(ret[0], self.article)

    def test_get_pubdate(self):
        """ test the return value of pubdate """

        ref = Article.objects.get(pk=self.article.pk).pubdate
        article = self.articlefeed.items()[0]
        ret = self.articlefeed.item_pubdate(item=article)
        self.assertEqual(ret.date(), ref.date())

    def test_get_title(self):
        """ test the return value of title """

        ref = self.article.title
        article = self.articlefeed.items()[0]
        ret = self.articlefeed.item_title(item=article)
        self.assertEqual(ret, ref)

    def test_get_description(self):
        """ test the return value of description """

        ref = self.article.description
        article = self.articlefeed.items()[0]
        ret = self.articlefeed.item_description(item=article)
        self.assertEqual(ret, ref)

    def test_get_author_name(self):
        """ test the return value of author name """

        ref = self.user_author.username
        article = self.articlefeed.items()[0]
        ret = self.articlefeed.item_author_name(item=article)
        self.assertEqual(ret, ref)

    def test_get_item_link(self):
        """ test the return value of item link """

        ref = self.article.get_absolute_url_online()
        article = self.articlefeed.items()[0]
        ret = self.articlefeed.item_link(item=article)
        self.assertEqual(ret, ref)

    def tearDown(self):
        if os.path.isdir(settings.ZDS_APP['article']['repo_path']):
            shutil.rmtree(settings.ZDS_APP['article']['repo_path'])
        if os.path.isdir(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)
