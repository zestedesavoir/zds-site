# coding: utf-8

from django.core.urlresolvers import reverse
from django.test import TestCase

from zds.member.factories import UserFactory

class MPTests(TestCase):
    
    def setUp(self):
        self.user1 = UserFactory()
        log = self.client.login(username=self.user1.username, password='hostel77')
        self.assertEqual(log, True)
        
    def test_mp_from_profile(self):
        '''
        Test: Send a MP from a user profile
        '''
        # User to send the MP
        user2 = UserFactory()
        
        # Test if user is correctly added to the MP 
        result = self.client.get(
                        reverse('zds.mp.views.new') + '?username={0}'.format(user2.username),
                        )
        
        # Check username in new MP page
        self.assertContains(result, user2.username)
