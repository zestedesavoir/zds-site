# coding: utf-8

from django.core.urlresolvers import reverse

from django.test import TestCase

from zds.article.models import Article
from zds.member.factories import UserFactory


class ArticleTests(TestCase):
    
    def setUp(self):
        self.user = UserFactory()
        
        login_check = self.client.login(username=self.user.username, password='hostel77')
        self.assertEqual(login_check, True)
    
    def test_mandatory_fields(self):
        '''
        Test handeling of mandatory fields
        No article can be created if mandatory fields are empty or contains only non-printable characters
        '''
        # Empty fields
        response = self.client.post(
            reverse('zds.article.views.new'), 
            {
            },
            follow=False)        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Article.objects.all().count(), 0)
        
        # Blank data
        response = self.client.post(
            reverse('zds.article.views.new'), 
            {
                'title': u' ',
                'description': u' ',
                'text': u' ',
            },
            follow=False)        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Article.objects.all().count(), 0)