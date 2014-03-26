# coding: utf-8

from django.contrib.auth.models import User
from django.test import TestCase
from django.conf import settings
from django.core.urlresolvers import reverse

from zds.member.factories import *
from zds.forum.factories import *
from .models import Post, Forum, Topic, Category
from zds.utils.models import CommentLike, CommentDislike 


class ForumMemberTests(TestCase):
    
    def setUp(self):
        
        settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
        
        self.category1 = CategoryFactory(position=1)
        self.category2 = CategoryFactory(position=2)
        self.category3 = CategoryFactory(position=3)
        self.forum11 = ForumFactory(category=self.category1,position_in_category=1)
        self.forum12 = ForumFactory(category=self.category1,position_in_category=2)
        self.forum13 = ForumFactory(category=self.category1,position_in_category=3)
        self.forum21 = ForumFactory(category=self.category2,position_in_category=1)
        self.forum22 = ForumFactory(category=self.category2,position_in_category=2)
        self.user = UserFactory()
        log = self.client.login(username=self.user.username, password='hostel77')
        self.assertEqual(log, True)
        
    
    def test_create_topic(self):
        '''
        To test all aspects of topic's creation by member
        '''
        result = self.client.post(
                        reverse('zds.forum.views.new')+'?forum={0}'.format(self.forum12.pk), 
                        {'title': u'Un autre sujet',
                          'subtitle': u'Encore ces lombards en plein été',
                          'text': u'C\'est tout simplement l\'histoire de la ville de Paris que je voudrais vous conter '
                        },
                        follow=False)
        self.assertEqual(result.status_code, 302)
        
        #check topic's number
        self.assertEqual(Topic.objects.all().count(), 1)
        topic = Topic.objects.get(pk=1)
        #check post's number
        self.assertEqual(Post.objects.all().count(), 1)
        post = Post.objects.get(pk=1)
        
        #check topic and post
        self.assertEqual(post.topic, topic)

        #check position
        self.assertEqual(post.position, 1)
        
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.editor, None)
        self.assertNotEqual(post.ip_address, None)
        self.assertNotEqual(post.text_html, None)
        self.assertEqual(post.like, 0)
        self.assertEqual(post.dislike, 0)
        self.assertEqual(post.is_visible, True)
        
        #check last message
        self.assertEqual(topic.last_message, post)
    
    def test_answer(self):
        '''
        To test all aspects of answer
        '''
        user1 = UserFactory()
        topic1 = TopicFactory(forum=self.forum11, author=self.user)
        post1 = PostFactory(topic=topic1, author=self.user, position = 1)
        post2 = PostFactory(topic=topic1, author=self.user, position = 2)
        post3 = PostFactory(topic=topic1, author=user1, position = 3)
        
        result = self.client.post(
                        reverse('zds.forum.views.answer')+'?sujet={0}'.format(topic1.pk), 
                        {
                          'last_post' : topic1.last_message.pk,
                          'text': u'C\'est tout simplement l\'histoire de la ville de Paris que je voudrais vous conter '
                        },
                        follow=False)
        
        
        self.assertEqual(result.status_code, 302)
        
        #check topic's number
        self.assertEqual(Topic.objects.all().count(), 1)

        #check post's number
        self.assertEqual(Post.objects.all().count(), 4)

        #check topic and post
        self.assertEqual(post1.topic, topic1)
        self.assertEqual(post2.topic, topic1)
        self.assertEqual(post3.topic, topic1)
        
        #check values
        self.assertEqual(Post.objects.get(pk=4).topic, topic1)
        self.assertEqual(Post.objects.get(pk=4).position, 4)
        self.assertEqual(Post.objects.get(pk=4).editor, None)        
        self.assertEqual(Post.objects.get(pk=4).text, u'C\'est tout simplement l\'histoire de la ville de Paris que je voudrais vous conter ')
        
        
    def test_edit_main_post(self):
        '''
        To test all aspects of the edition of main post by member
        '''
        topic1 = TopicFactory(forum=self.forum11, author=self.user)
        post1 = PostFactory(topic=topic1, author=self.user, position = 1)
        topic2 = TopicFactory(forum=self.forum12, author=self.user)
        post2 = PostFactory(topic=topic2, author=self.user, position = 1)
        topic3 = TopicFactory(forum=self.forum21, author=self.user)
        post3 = PostFactory(topic=topic3, author=self.user, position = 1)
        
        result = self.client.post(
                        reverse('zds.forum.views.edit_post')+'?message={0}'.format(post1.pk), 
                        {'title': u'Un autre sujet',
                          'subtitle': u'Encore ces lombards en plein été',
                          'text': u'C\'est tout simplement l\'histoire de la ville de Paris que je voudrais vous conter '
                        },
                        follow=False)
        
        self.assertEqual(result.status_code, 302)
        
        #check topic's number
        self.assertEqual(Topic.objects.all().count(), 3)

        #check post's number
        self.assertEqual(Post.objects.all().count(), 3)

        #check topic and post
        self.assertEqual(post1.topic, topic1)
        self.assertEqual(post2.topic, topic2)
        self.assertEqual(post3.topic, topic3)
        
        #check values
        self.assertEqual(Topic.objects.get(pk=topic1.pk).title, u'Un autre sujet')
        self.assertEqual(Topic.objects.get(pk=topic1.pk).subtitle, u'Encore ces lombards en plein été')
        self.assertEqual(Post.objects.get(pk=post1.pk).text, u'C\'est tout simplement l\'histoire de la ville de Paris que je voudrais vous conter ')
        
        #check edit data
        self.assertEqual(Post.objects.get(pk=post1.pk).editor, self.user)
    
    def test_edit_post(self):
        '''
        To test all aspects of the edition of simple post by member
        '''
        topic1 = TopicFactory(forum=self.forum11, author=self.user)
        post1 = PostFactory(topic=topic1, author=self.user, position = 1)
        post2 = PostFactory(topic=topic1, author=self.user, position = 2)
        post3 = PostFactory(topic=topic1, author=self.user, position = 3)
        
        result = self.client.post(
                        reverse('zds.forum.views.edit_post')+'?message={0}'.format(post2.pk), 
                        {
                          'text': u'C\'est tout simplement l\'histoire de la ville de Paris que je voudrais vous conter '
                        },
                        follow=False)
        
        self.assertEqual(result.status_code, 302)
        
        #check topic's number
        self.assertEqual(Topic.objects.all().count(), 1)

        #check post's number
        self.assertEqual(Post.objects.all().count(), 3)

        #check topic and post
        self.assertEqual(post1.topic, topic1)
        self.assertEqual(post2.topic, topic1)
        self.assertEqual(post3.topic, topic1)
        
        #check values
        self.assertEqual(Post.objects.get(pk=post2.pk).text, u'C\'est tout simplement l\'histoire de la ville de Paris que je voudrais vous conter ')
        
        #check edit data
        self.assertEqual(Post.objects.get(pk=post2.pk).editor, self.user)
    
    def test_quote_post(self):
        '''
        To test when a member quote anyone post
        '''
        user1 = UserFactory()
        topic1 = TopicFactory(forum=self.forum11, author=self.user)
        post1 = PostFactory(topic=topic1, author=self.user, position = 1)
        post2 = PostFactory(topic=topic1, author=user1, position = 2)
        post3 = PostFactory(topic=topic1, author=user1, position = 3)
        
        result = self.client.get(
                        reverse('zds.forum.views.answer')+'?sujet={0}&cite={0}'.format(topic1.pk, post2.pk),
                        follow=True)
        
        self.assertEqual(result.status_code, 200)
    
    def test_like_post(self):
        '''
        Test when a member like any post
        '''
        user1 = UserFactory()
        topic1 = TopicFactory(forum=self.forum11, author=self.user)
        post1 = PostFactory(topic=topic1, author=self.user, position = 1)
        post2 = PostFactory(topic=topic1, author=user1, position = 2)
        post3 = PostFactory(topic=topic1, author=self.user, position = 3)
        
        result = self.client.get(
                        reverse('zds.forum.views.like_post')+'?message={0}'.format(post2.pk),
                        follow=False)
        
        self.assertEqual(result.status_code, 302)
        self.assertEqual(CommentLike.objects.all().count(), 1)
        self.assertEqual(Post.objects.get(pk=post1.pk).like, 0)
        self.assertEqual(Post.objects.get(pk=post2.pk).like, 1)
        self.assertEqual(Post.objects.get(pk=post3.pk).like, 0)
        self.assertEqual(Post.objects.get(pk=post1.pk).dislike, 0)
        self.assertEqual(Post.objects.get(pk=post2.pk).dislike, 0)
        self.assertEqual(Post.objects.get(pk=post3.pk).dislike, 0)
        self.assertEqual(CommentLike.objects.filter(comments__pk=post1.pk).all().count(), 0)
        self.assertEqual(CommentLike.objects.filter(comments__pk=post2.pk).all().count(), 1)
        self.assertEqual(CommentLike.objects.filter(comments__pk=post3.pk).all().count(), 0)
        
        result = self.client.get(
                        reverse('zds.forum.views.like_post')+'?message={0}'.format(post1.pk),
                        follow=False)
        
        self.assertEqual(result.status_code, 302)
        self.assertEqual(CommentLike.objects.all().count(), 1)
        self.assertEqual(Post.objects.get(pk=post1.pk).like, 0)
        self.assertEqual(Post.objects.get(pk=post2.pk).like, 1)
        self.assertEqual(Post.objects.get(pk=post3.pk).like, 0)
        self.assertEqual(Post.objects.get(pk=post1.pk).dislike, 0)
        self.assertEqual(Post.objects.get(pk=post2.pk).dislike, 0)
        self.assertEqual(Post.objects.get(pk=post3.pk).dislike, 0)
        self.assertEqual(CommentLike.objects.filter(comments__pk=post1.pk).all().count(), 0)
        self.assertEqual(CommentLike.objects.filter(comments__pk=post2.pk).all().count(), 1)
        self.assertEqual(CommentLike.objects.filter(comments__pk=post3.pk).all().count(), 0)
    
    def test_dislike_post(self):
        '''
        Test when a member dislike any post
        '''
        user1 = UserFactory()
        topic1 = TopicFactory(forum=self.forum11, author=self.user)
        post1 = PostFactory(topic=topic1, author=self.user, position = 1)
        post2 = PostFactory(topic=topic1, author=user1, position = 2)
        post3 = PostFactory(topic=topic1, author=self.user, position = 3)
        
        result = self.client.get(
                        reverse('zds.forum.views.dislike_post')+'?message={0}'.format(post2.pk),
                        follow=False)
        
        self.assertEqual(result.status_code, 302)
        self.assertEqual(CommentDislike.objects.all().count(), 1)
        self.assertEqual(Post.objects.get(pk=post1.pk).like, 0)
        self.assertEqual(Post.objects.get(pk=post2.pk).like, 0)
        self.assertEqual(Post.objects.get(pk=post3.pk).like, 0)
        self.assertEqual(Post.objects.get(pk=post1.pk).dislike, 0)
        self.assertEqual(Post.objects.get(pk=post2.pk).dislike, 1)
        self.assertEqual(Post.objects.get(pk=post3.pk).dislike, 0)
        self.assertEqual(CommentDislike.objects.filter(comments__pk=post1.pk).all().count(), 0)
        self.assertEqual(CommentDislike.objects.filter(comments__pk=post2.pk).all().count(), 1)
        self.assertEqual(CommentDislike.objects.filter(comments__pk=post3.pk).all().count(), 0)
        
        result = self.client.get(
                        reverse('zds.forum.views.like_post')+'?message={0}'.format(post1.pk),
                        follow=False)
        
        self.assertEqual(result.status_code, 302)
        self.assertEqual(CommentDislike.objects.all().count(), 1)
        self.assertEqual(Post.objects.get(pk=post1.pk).like, 0)
        self.assertEqual(Post.objects.get(pk=post2.pk).like, 0)
        self.assertEqual(Post.objects.get(pk=post3.pk).like, 0)
        self.assertEqual(Post.objects.get(pk=post1.pk).dislike, 0)
        self.assertEqual(Post.objects.get(pk=post2.pk).dislike, 1)
        self.assertEqual(Post.objects.get(pk=post3.pk).dislike, 0)
        self.assertEqual(CommentDislike.objects.filter(comments__pk=post1.pk).all().count(), 0)
        self.assertEqual(CommentDislike.objects.filter(comments__pk=post2.pk).all().count(), 1)
        self.assertEqual(CommentDislike.objects.filter(comments__pk=post3.pk).all().count(), 0)
    
    def test_useful_post(self):
        '''
        To test when a member mark a post is usefull
        '''
        user1 = UserFactory()
        topic1 = TopicFactory(forum=self.forum11, author=self.user)
        post1 = PostFactory(topic=topic1, author=self.user, position = 1)
        post2 = PostFactory(topic=topic1, author=user1, position = 2)
        post3 = PostFactory(topic=topic1, author=user1, position = 3)
        
        result = self.client.get(
                        reverse('zds.forum.views.useful_post')+'?message={0}'.format(post2.pk),
                        follow=False)
        
        self.assertEqual(result.status_code, 302)
        
        self.assertEqual(Post.objects.get(pk=post1.pk).is_useful, False)
        self.assertEqual(Post.objects.get(pk=post2.pk).is_useful, True)
        self.assertEqual(Post.objects.get(pk=post3.pk).is_useful, False)
        
        #useful the first post
        result = self.client.get(
                        reverse('zds.forum.views.useful_post')+'?message={0}'.format(post1.pk),
                        follow=False)
        self.assertEqual(result.status_code, 404)
        
        self.assertEqual(Post.objects.get(pk=post1.pk).is_useful, False)
        self.assertEqual(Post.objects.get(pk=post2.pk).is_useful, True)
        self.assertEqual(Post.objects.get(pk=post3.pk).is_useful, False)
        
        #useful if you aren't author
        topic2 = TopicFactory(forum=self.forum11, author=user1)
        post4 = PostFactory(topic=topic1, author=user1, position = 1)
        post5 = PostFactory(topic=topic1, author=self.user, position = 2)
        
        result = self.client.get(
                        reverse('zds.forum.views.useful_post')+'?message={0}'.format(post5.pk),
                        follow=False)
        
        self.assertEqual(result.status_code, 404)
        
        self.assertEqual(Post.objects.get(pk=post4.pk).is_useful, False)
        self.assertEqual(Post.objects.get(pk=post5.pk).is_useful, False)
        
    def test_move_topic(self):
        '''
        Test topic move
        '''
        user1 = UserFactory()
        topic1 = TopicFactory(forum=self.forum11, author=self.user)
        post1 = PostFactory(topic=topic1, author=self.user, position = 1)
        post2 = PostFactory(topic=topic1, author=user1, position = 2)
        post3 = PostFactory(topic=topic1, author=self.user, position = 3)
        
        #not staff member can't move topic
        result = self.client.post(
                        reverse('zds.forum.views.move_topic')+'?sujet={0}'.format(topic1.pk),
                        {
                          'forum': self.forum12
                        },
                        follow=False)
        
        self.assertEqual(result.status_code, 403)
        
        #test with staff
        staff1 = StaffFactory()
        self.assertEqual(self.client.login(username=staff1.username, password='hostel77'), True)
        
        result = self.client.post(
                        reverse('zds.forum.views.move_topic')+'?sujet={0}'.format(topic1.pk),
                        {
                          'forum': self.forum12.pk
                        },
                        follow=False)
        
        self.assertEqual(result.status_code, 302)
        
        #check value
        self.assertEqual(Topic.objects.get(pk=topic1.pk).forum.pk, self.forum12.pk)
                
        