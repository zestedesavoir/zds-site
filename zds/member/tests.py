# coding: utf-8

from django.contrib.auth.models import User
from django.test import TestCase
from django.conf import settings
from django.core.urlresolvers import reverse

from zds.member.factories import *
from zds.forum.factories import *
from .models import Profile, TokenRegister
from django.core import mail


class MemberTests(TestCase):
    
    def setUp(self):
        settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
        
    
    def test_login(self):
        '''
        To test user login
        '''
        user = UserFactory()
        
        result = self.client.post(
                        reverse('zds.member.views.login_view'), 
                        {'username': 'firm1', 'password': 'hostel', 'remember': 'remember'},
                        follow=False)
        #bad password then no redirection
        self.assertEqual(result.status_code, 200)
        
        result = self.client.post(
                        reverse('zds.member.views.login_view'), 
                        {'username': 'firm1','password': 'hostel77','remember': 'remember'},
                        follow=False)
        #good password then redirection
        self.assertEqual(result.status_code, 302)
        
    
    def test_register(self):
        '''
        To test user registration
        '''
        
        result = self.client.post(
                        reverse('zds.member.views.register_view'), 
                        {'username': 'firm1', 'password': 'flavour', 'password_confirm': 'flavour', 'email': 'firm1@zestedesavoir.com'},
                        follow=False)
        
        self.assertEqual(result.status_code, 200)
        
        #check email has been sent
        self.assertEquals(len(mail.outbox), 1)
        
        #clic on the link which has been sent in mail
        user = User.objects.get(username='firm1')
        self.assertEquals(user.is_active, False)
                          
        token = TokenRegister.objects.get(user=user)
        result = self.client.get(
                        settings.SITE_URL+token.get_absolute_url(),
                        follow=False)
        self.assertEqual(result.status_code, 200)
        
        self.assertEquals(User.objects.get(username='firm1').is_active, True)
        
        
        