from datetime import datetime, timedelta
from hashlib import md5

from django.conf import settings
from django.contrib.auth.models import Group
from django.test import TestCase

from zds.forum.tests.factories import ForumCategoryFactory, ForumFactory, PostFactory, TopicFactory
from zds.gallery.tests.factories import GalleryFactory, ImageFactory
from zds.member.models import Profile, TokenForgotPassword, TokenRegister
from zds.member.tests.factories import DevProfileFactory, ProfileFactory, StaffProfileFactory
from zds.notification.models import TopicAnswerSubscription
from zds.tutorialv2.tests import TutorialTestMixin, override_for_contents
from zds.tutorialv2.tests.factories import PublishableContentFactory, PublishedContentFactory
from zds.utils.models import Alert, Hat


@override_for_contents()
class MemberModelsTest(TutorialTestMixin, TestCase):
    def setUp(self):
        self.user1 = ProfileFactory()
        self.staff = StaffProfileFactory()

        # Create a forum for later test
        self.forumcat = ForumCategoryFactory()
        self.forum = ForumFactory(category=self.forumcat)
        self.forumtopic = TopicFactory(forum=self.forum, author=self.staff.user)

    def test_get_absolute_url_for_details_of_member(self):
        self.assertEqual(self.user1.get_absolute_url(), f"/@{self.user1.user.username}")

    def test_get_absolute_avatar_url(self):
        # if no url was specified -> nothing !
        self.assertEqual(self.user1.get_absolute_avatar_url(), None)

        # if an url is specified -> take it !
        user2 = ProfileFactory()
        testurl = "http://test.com/avatar.jpg"
        user2.avatar_url = testurl
        self.assertEqual(user2.get_absolute_avatar_url(), testurl)

        # if url is relative, send absolute url
        gallerie_avatar = GalleryFactory()
        image_avatar = ImageFactory(gallery=gallerie_avatar)
        user2.avatar_url = image_avatar.physical.url
        self.assertNotEqual(user2.get_absolute_avatar_url(), image_avatar.physical.url)
        self.assertIn(image_avatar.physical.url, user2.get_absolute_avatar_url())
        self.assertIn("http", user2.get_absolute_avatar_url())

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

    def test_get_tutos(self):
        # Start with 0
        self.assertEqual(len(self.user1.get_tutos()), 0)
        # Create Tuto !
        minituto = PublishableContentFactory(type="TUTORIAL")
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
        drafttuto = PublishableContentFactory(type="TUTORIAL")
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
        publictuto = PublishableContentFactory(type="TUTORIAL")
        publictuto.authors.add(self.user1.user)
        publictuto.gallery = GalleryFactory()
        publictuto.sha_public = "whatever"
        publictuto.save()
        # Should be 0 because publication was not used
        publictutos = self.user1.get_public_tutos()
        self.assertEqual(len(publictutos), 0)
        PublishedContentFactory(author_list=[self.user1.user])
        self.assertEqual(len(self.user1.get_public_tutos()), 1)

    def test_get_validate_tutos(self):
        # Start with 0
        self.assertEqual(len(self.user1.get_validate_tutos()), 0)
        # Create Tuto !
        validatetuto = PublishableContentFactory(type="TUTORIAL", author_list=[self.user1.user])
        validatetuto.sha_validation = "whatever"
        validatetuto.save()
        # Should be 1
        validatetutos = self.user1.get_validate_tutos()
        self.assertEqual(len(validatetutos), 1)
        self.assertEqual(validatetuto, validatetutos[0])

    def test_get_beta_tutos(self):
        # Start with 0
        self.assertEqual(len(self.user1.get_beta_tutos()), 0)
        # Create Tuto !
        betatetuto = PublishableContentFactory(type="TUTORIAL")
        betatetuto.authors.add(self.user1.user)
        betatetuto.gallery = GalleryFactory()
        betatetuto.sha_beta = "whatever"
        betatetuto.save()
        # Should be 1
        betatetutos = self.user1.get_beta_tutos()
        self.assertEqual(len(betatetutos), 1)
        self.assertEqual(betatetuto, betatetutos[0])

    def test_get_articles(self):
        # Start with 0
        self.assertEqual(len(self.user1.get_articles()), 0)
        # Create article !
        article = PublishableContentFactory(type="ARTICLE")
        article.authors.add(self.user1.user)
        article.save()
        # Should be 1
        articles = self.user1.get_articles()
        self.assertEqual(len(articles), 1)
        self.assertEqual(article, articles[0])

    def test_get_public_articles(self):
        # Start with 0
        self.assertEqual(len(self.user1.get_public_articles()), 0)
        # Create article !
        article = PublishableContentFactory(type="ARTICLE")
        article.authors.add(self.user1.user)
        article.sha_public = "whatever"
        article.save()
        # Should be 0
        articles = self.user1.get_public_articles()
        self.assertEqual(len(articles), 0)
        # Should be 1
        PublishedContentFactory(author_list=[self.user1.user], type="ARTICLE")
        self.assertEqual(len(self.user1.get_public_articles()), 1)
        self.assertEqual(len(self.user1.get_public_tutos()), 0)

    def test_get_validate_articles(self):
        # Start with 0
        self.assertEqual(len(self.user1.get_validate_articles()), 0)
        # Create article !
        article = PublishableContentFactory(type="ARTICLE")
        article.authors.add(self.user1.user)
        article.sha_validation = "whatever"
        article.save()
        # Should be 1
        articles = self.user1.get_validate_articles()
        self.assertEqual(len(articles), 1)
        self.assertEqual(article, articles[0])

    def test_get_draft_articles(self):
        # Start with 0
        self.assertEqual(len(self.user1.get_draft_articles()), 0)
        # Create article !
        article = PublishableContentFactory(type="ARTICLE")
        article.authors.add(self.user1.user)
        article.save()
        # Should be 1
        articles = self.user1.get_draft_articles()
        self.assertEqual(len(articles), 1)
        self.assertEqual(article, articles[0])

    def test_get_beta_articles(self):
        # Start with 0
        self.assertEqual(len(self.user1.get_beta_articles()), 0)
        # Create article !
        article = PublishableContentFactory(type="ARTICLE")
        article.authors.add(self.user1.user)
        article.sha_beta = "whatever"
        article.save()
        # Should be 1
        articles = self.user1.get_beta_articles()
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

    def test_get_hidden_by_staff_posts_count(self):
        # Start with 0
        self.assertEqual(self.user1.get_hidden_by_staff_posts_count(), 0)
        # Post and hide it by poster
        PostFactory(topic=self.forumtopic, author=self.user1.user, position=1, is_visible=False, editor=self.user1.user)
        # Should be 0
        self.assertEqual(self.user1.get_hidden_by_staff_posts_count(), 0)
        # Post and hide it by staff
        PostFactory(topic=self.forumtopic, author=self.user1.user, position=1, is_visible=False, editor=self.staff.user)
        # Should be 1
        self.assertEqual(self.user1.get_hidden_by_staff_posts_count(), 1)

    def test_get_hidden_by_staff_posts_count_staff_poster(self):
        # Start with 0
        self.assertEqual(self.staff.get_hidden_by_staff_posts_count(), 0)
        # Post and hide it by poster which is staff
        PostFactory(topic=self.forumtopic, author=self.staff.user, position=1, is_visible=False, editor=self.staff.user)
        # Should be 0 because even if poster is staff, he is the poster
        self.assertEqual(self.staff.get_hidden_by_staff_posts_count(), 0)

    def test_get_active_alerts_count(self):
        # Start with 0
        self.assertEqual(self.user1.get_active_alerts_count(), 0)
        # Post and Alert it !
        post = PostFactory(topic=self.forumtopic, author=self.user1.user, position=1)
        Alert.objects.create(author=self.user1.user, comment=post, scope="FORUM", pubdate=datetime.now())
        # Should be 1
        self.assertEqual(self.user1.get_active_alerts_count(), 1)

    def test_can_read_now(self):
        profile = ProfileFactory()
        profile.is_active = True
        profile.can_read = True
        self.assertTrue(profile.can_read_now())

        # Was banned in the past, ban no longer active
        profile = ProfileFactory()
        profile.end_ban_read = datetime.now() - timedelta(days=1)
        self.assertTrue(profile.can_read_now())

        profile = ProfileFactory()
        profile.is_active = True
        profile.can_read = False
        self.assertFalse(profile.can_read_now())

        # Ban is active
        profile = ProfileFactory()
        profile.is_active = True
        profile.can_read = False
        profile.end_ban_read = datetime.now() + timedelta(days=1)
        self.assertFalse(profile.can_read_now())

        self.user1.user.is_active = False
        self.assertFalse(self.user1.can_read_now())

    def test_can_write_now(self):
        self.user1.user.is_active = True
        self.user1.user.can_write = True
        self.assertTrue(self.user1.can_write_now())

        # Was banned in the past, ban no longer active
        profile = ProfileFactory()
        profile.can_write = True
        profile.end_ban_read = datetime.now() - timedelta(days=1)
        self.assertTrue(profile.can_write_now())

        profile = ProfileFactory()
        profile.can_write = False
        profile.is_active = True
        self.assertFalse(profile.can_write_now())

        # Ban is active
        profile = ProfileFactory()
        profile.can_write = False
        profile.end_ban_write = datetime.now() + timedelta(days=1)
        self.assertFalse(profile.can_write_now())

        self.user1.user.is_active = False
        self.user1.user.can_write = True
        self.assertFalse(self.user1.can_write_now())

    def test_get_followed_topics(self):
        # Start with 0
        self.assertEqual(len(TopicAnswerSubscription.objects.get_objects_followed_by(self.user1.user)), 0)
        self.assertEqual(self.user1.get_followed_topic_count(), 0)
        # Follow !
        TopicAnswerSubscription.objects.toggle_follow(self.forumtopic, self.user1.user)
        # Should be 1
        topicsfollowed = TopicAnswerSubscription.objects.get_objects_followed_by(self.user1.user)
        self.assertEqual(len(topicsfollowed), 1)
        self.assertEqual(self.forumtopic, topicsfollowed[0])
        self.assertEqual(self.user1.get_followed_topic_count(), 1)
        self.assertIn(self.forumtopic, self.user1.get_followed_topics())

    def test_get_city_with_wrong_ip(self):
        # Set a local IP to the user
        self.user1.last_ip_address = "127.0.0.1"
        # Then the get_city is not found and return empty string
        self.assertEqual("", self.user1.get_city())

        # Same goes for IPV6
        # Set a local IP to the user
        self.user1.last_ip_address = "0000:0000:0000:0000:0000:0000:0000:0001"
        # Then the get_city is not found and return empty string
        self.assertEqual("", self.user1.get_city())

    def test_remove_token_on_removing_from_dev_group(self):
        dev = DevProfileFactory()
        dev.github_token = "test"
        dev.save()
        dev.user.save()

        self.assertEqual("test", dev.github_token)

        # remove dev from dev group
        dev.user.groups.clear()
        dev.user.save()

        self.assertEqual("", dev.github_token)

    def test_reachable_manager(self):
        # profile types
        profile_normal = ProfileFactory()
        profile_superuser = ProfileFactory()
        profile_superuser.user.is_superuser = True
        profile_superuser.user.save()
        profile_inactive = ProfileFactory()
        profile_inactive.user.is_active = False
        profile_inactive.user.save()
        profile_bot = ProfileFactory()
        profile_bot.user.username = settings.ZDS_APP["member"]["bot_account"]
        profile_bot.user.save()
        profile_anonymous = ProfileFactory()
        profile_anonymous.user.username = settings.ZDS_APP["member"]["anonymous_account"]
        profile_anonymous.user.save()
        profile_external = ProfileFactory()
        profile_external.user.username = settings.ZDS_APP["member"]["external_account"]
        profile_external.user.save()
        profile_ban_def = ProfileFactory()
        profile_ban_def.can_read = False
        profile_ban_def.can_write = False
        profile_ban_def.save()
        profile_ban_temp = ProfileFactory()
        profile_ban_temp.can_read = False
        profile_ban_temp.can_write = False
        profile_ban_temp.end_ban_read = datetime.now() + timedelta(days=1)
        profile_ban_temp.save()
        profile_unban = ProfileFactory()
        profile_unban.can_read = False
        profile_unban.can_write = False
        profile_unban.end_ban_read = datetime.now() - timedelta(days=1)
        profile_unban.save()
        profile_ls_def = ProfileFactory()
        profile_ls_def.can_write = False
        profile_ls_def.save()
        profile_ls_temp = ProfileFactory()
        profile_ls_temp.can_write = False
        profile_ls_temp.end_ban_write = datetime.now() + timedelta(days=1)
        profile_ls_temp.save()

        # groups

        bot = Group(name=settings.ZDS_APP["member"]["bot_group"])
        bot.save()

        # associate account to groups
        bot.user_set.add(profile_anonymous.user)
        bot.user_set.add(profile_external.user)
        bot.user_set.add(profile_bot.user)
        bot.save()

        # test reachable user
        profiles_reacheable = Profile.objects.contactable_members().all()
        self.assertIn(profile_normal, profiles_reacheable)
        self.assertIn(profile_superuser, profiles_reacheable)
        self.assertNotIn(profile_inactive, profiles_reacheable)
        self.assertNotIn(profile_anonymous, profiles_reacheable)
        self.assertNotIn(profile_external, profiles_reacheable)
        self.assertNotIn(profile_bot, profiles_reacheable)
        self.assertIn(profile_unban, profiles_reacheable)
        self.assertNotIn(profile_ban_def, profiles_reacheable)
        self.assertNotIn(profile_ban_temp, profiles_reacheable)
        self.assertIn(profile_ls_def, profiles_reacheable)
        self.assertIn(profile_ls_temp, profiles_reacheable)

    def test_remove_hats_linked_to_group(self):
        # create a hat linked to a group
        hat_name = "Test hat"
        hat, _ = Hat.objects.get_or_create(name__iexact=hat_name, defaults={"name": hat_name})
        group, _ = Group.objects.get_or_create(name="test_hat")
        hat.group = group
        hat.save()
        # add it to a user
        self.user1.hats.add(hat)
        self.user1.save()
        # the user shound't have the hat through their profile
        self.assertNotIn(hat, self.user1.hats.all())


class TestTokenForgotPassword(TestCase):
    def setUp(self):
        self.user1 = ProfileFactory()
        self.token = TokenForgotPassword.objects.create(user=self.user1.user, token="abcde", date_end=datetime.now())

    def test_get_absolute_url(self):
        self.assertEqual(self.token.get_absolute_url(), f"/membres/new_password/?token={self.token.token}")


class TestTokenRegister(TestCase):
    def setUp(self):
        self.user1 = ProfileFactory()
        self.token = TokenRegister.objects.create(user=self.user1.user, token="abcde", date_end=datetime.now())

    def test_get_absolute_url(self):
        self.assertEqual(self.token.get_absolute_url(), f"/membres/activation/?token={self.token.token}")
