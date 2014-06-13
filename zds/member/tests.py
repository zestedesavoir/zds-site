# coding: utf-8

from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase

from zds.member.factories import ProfileFactory, StaffProfileFactory
from zds.member.forms import RegisterForm, ChangeUserForm, \
                            ChangePasswordForm
from zds.member.models import Profile

from .models import TokenRegister, Ban


class MemberTests(TestCase):

    def setUp(self):
        settings.EMAIL_BACKEND = \
            'django.core.mail.backends.locmem.EmailBackend'
        self.mas = ProfileFactory()
        settings.BOT_ACCOUNT = self.mas.user.username

    def test_login(self):
        """To test user login."""
        user = ProfileFactory()

        result = self.client.post(
            reverse('zds.member.views.login_view'),
            {'username': user.user.username,
             'password': 'hostel',
             'remember': 'remember'},
            follow=False)
        # bad password then no redirection
        self.assertEqual(result.status_code, 200)

        result = self.client.post(
            reverse('zds.member.views.login_view'),
            {'username': user.user.username,
             'password': 'hostel77',
             'remember': 'remember'},
            follow=False)
        # good password then redirection
        self.assertEqual(result.status_code, 302)

    def test_register(self):
        """To test user registration."""

        result = self.client.post(
            reverse('zds.member.views.register_view'),
            {
                'username': 'firm1',
                'password': 'flavour',
                'password_confirm': 'flavour',
                'email': 'firm1@zestedesavoir.com'},
            follow=False)

        self.assertEqual(result.status_code, 200)

        # check email has been sent
        self.assertEquals(len(mail.outbox), 1)

        # clic on the link which has been sent in mail
        user = User.objects.get(username='firm1')
        self.assertFalse(user.is_active)

        token = TokenRegister.objects.get(user=user)
        result = self.client.get(
            settings.SITE_URL + token.get_absolute_url(),
            follow=False)

        self.assertEqual(result.status_code, 200)
        self.assertEquals(len(mail.outbox), 2)

        self.assertTrue(User.objects.get(username='firm1').is_active)

        # From this point we have a valid user (firm1 / firm1@zestedesavoir.com)

        # Now let's test all the failing cases !!

        # 1. If passwords don't match
        form_data = {
            'username': 'TheUsername',
            'password': 'password',
            'password_confirm': 'flavour',
            'email': 'email@zestedesavoir.com'
        }
        form = RegisterForm(data=form_data)
        self.assertFalse(form.is_valid())

        # 2. If passwords are too shorts
        form_data = {
            'username': 'TheUsername',
            'password': 'pass',
            'password_confirm': 'pass',
            'email': 'email@zestedesavoir.com'
        }
        form = RegisterForm(data=form_data)
        self.assertFalse(form.is_valid())

        # 3. If passwords are equal to username
        form_data = {
            'username': 'TheUsername',
            'password': 'TheUsername',
            'password_confirm': 'TheUsername',
            'email': 'email@zestedesavoir.com'
        }
        form = RegisterForm(data=form_data)
        self.assertFalse(form.is_valid())

        # 4. If there is no username
        form_data = {
            'username': '',
            'password': 'password',
            'password_confirm': 'password',
            'email': 'email@zestedesavoir.com'
        }
        form = RegisterForm(data=form_data)
        self.assertFalse(form.is_valid())

        # 5. If there is no email
        form_data = {
            'username': 'TheUsername',
            'password': 'password',
            'password_confirm': 'password',
            'email': ''
        }
        form = RegisterForm(data=form_data)
        self.assertFalse(form.is_valid())

        # 6. If the username is already taken
        form_data = {
            'username': 'firm1',
            'password': 'password',
            'password_confirm': 'password',
            'email': 'email@zestedesavoir.com'
        }
        form = RegisterForm(data=form_data)
        self.assertFalse(form.is_valid())

        # 7. If the email is already taken
        form_data = {
            'username': 'TheUsername',
            'password': 'password',
            'password_confirm': 'password',
            'email': 'firm1@zestedesavoir.com'
        }
        form = RegisterForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_sanctions(self):
        """Test various sanctions."""

        staff = StaffProfileFactory()
        login_check = self.client.login(
            username=staff.user.username,
            password='hostel77')
        self.assertEqual(login_check, True)

        # Test: LS
        user_ls = ProfileFactory()
        result = self.client.post(
            reverse(
                'zds.member.views.modify_profile', kwargs={
                    'user_pk': user_ls.user.id}), {
                'ls': '', 'ls-text': 'Texte de test pour LS'}, follow=False)
        user = Profile.objects.get(id=user_ls.id)    # Refresh profile from DB
        self.assertEqual(result.status_code, 302)
        self.assertFalse(user.can_write)
        self.assertTrue(user.can_read)
        self.assertIsNone(user.end_ban_write)
        self.assertIsNone(user.end_ban_read)
        ban = Ban.objects.filter(user__id=user.user.id).order_by('-pubdate')[0]
        self.assertEqual(ban.type, 'Lecture Seule')
        self.assertEqual(ban.text, 'Texte de test pour LS')
        self.assertEquals(len(mail.outbox), 1)

        # Test: Un-LS
        result = self.client.post(
            reverse(
                'zds.member.views.modify_profile', kwargs={
                    'user_pk': user_ls.user.id}), {
                'un-ls': '', 'unls-text': 'Texte de test pour un-LS'},
            follow=False)
        user = Profile.objects.get(id=user_ls.id)    # Refresh profile from DB
        self.assertEqual(result.status_code, 302)
        self.assertTrue(user.can_write)
        self.assertTrue(user.can_read)
        self.assertIsNone(user.end_ban_write)
        self.assertIsNone(user.end_ban_read)
        ban = Ban.objects.filter(user__id=user.user.id).order_by('-id')[0]
        self.assertEqual(ban.type, u'Autorisation d\'écrire')
        self.assertEqual(ban.text, 'Texte de test pour un-LS')
        self.assertEquals(len(mail.outbox), 2)

        # Test: LS temp
        user_ls_temp = ProfileFactory()
        result = self.client.post(
            reverse(
                'zds.member.views.modify_profile', kwargs={
                    'user_pk': user_ls_temp.user.id}), {
                'ls-temp': '', 'ls-jrs': 10,
                'ls-temp-text': 'Texte de test pour LS TEMP'},
            follow=False)
        user = Profile.objects.get(
            id=user_ls_temp.id)    # Refresh profile from DB
        self.assertEqual(result.status_code, 302)
        self.assertFalse(user.can_write)
        self.assertTrue(user.can_read)
        self.assertIsNotNone(user.end_ban_write)
        self.assertIsNone(user.end_ban_read)
        ban = Ban.objects.filter(user__id=user.user.id).order_by('-id')[0]
        self.assertEqual(ban.type, 'Lecture Seule Temporaire')
        self.assertEqual(ban.text, 'Texte de test pour LS TEMP')
        self.assertEquals(len(mail.outbox), 3)

        # Test: BAN
        user_ban = ProfileFactory()
        result = self.client.post(
            reverse(
                'zds.member.views.modify_profile', kwargs={
                    'user_pk': user_ban.user.id}), {
                'ban': '', 'ban-text': 'Texte de test pour BAN'}, follow=False)
        user = Profile.objects.get(id=user_ban.id)    # Refresh profile from DB
        self.assertEqual(result.status_code, 302)
        self.assertTrue(user.can_write)
        self.assertFalse(user.can_read)
        self.assertIsNone(user.end_ban_write)
        self.assertIsNone(user.end_ban_read)
        ban = Ban.objects.filter(user__id=user.user.id).order_by('-id')[0]
        self.assertEqual(ban.type, u'Ban définitif')
        self.assertEqual(ban.text, 'Texte de test pour BAN')
        self.assertEquals(len(mail.outbox), 4)

        # Test: un-BAN
        result = self.client.post(
            reverse(
                'zds.member.views.modify_profile', kwargs={
                    'user_pk': user_ban.user.id}),
            {'un-ban': '',
             'unban-text': 'Texte de test pour BAN'},
            follow=False)
        user = Profile.objects.get(id=user_ban.id)    # Refresh profile from DB
        self.assertEqual(result.status_code, 302)
        self.assertTrue(user.can_write)
        self.assertTrue(user.can_read)
        self.assertIsNone(user.end_ban_write)
        self.assertIsNone(user.end_ban_read)
        ban = Ban.objects.filter(user__id=user.user.id).order_by('-id')[0]
        self.assertEqual(ban.type, 'Autorisation de se connecter')
        self.assertEqual(ban.text, 'Texte de test pour BAN')
        self.assertEquals(len(mail.outbox), 5)

        # Test: BAN temp
        user_ban_temp = ProfileFactory()
        result = self.client.post(
            reverse('zds.member.views.modify_profile',
                    kwargs={'user_pk': user_ban_temp.user.id}),
            {'ban-temp': '', 'ban-jrs': 10,
             'ban-temp-text': 'Texte de test pour BAN TEMP'},
            follow=False)
        user = Profile.objects.get(
            id=user_ban_temp.id)    # Refresh profile from DB
        self.assertEqual(result.status_code, 302)
        self.assertTrue(user.can_write)
        self.assertFalse(user.can_read)
        self.assertIsNone(user.end_ban_write)
        self.assertIsNotNone(user.end_ban_read)
        ban = Ban.objects.filter(user__id=user.user.id).order_by('-id')[0]
        self.assertEqual(ban.type, 'Ban Temporaire')
        self.assertEqual(ban.text, 'Texte de test pour BAN TEMP')
        self.assertEquals(len(mail.outbox), 6)
    
    def test_update_password(self):
        """Test the password"""
        
        # create dummy user (to test)
        user = ProfileFactory()
        login_check = self.client.login(
            username=user.user.username,
            password='hostel77')
        self.assertTrue(login_check)
        
        # 1. If passwords don't match
        form_data = {
            'password_old': 'hostel77',
            'password_new': 'ThePassword1234',
            'password_confirm': 'TheWrongPassword'
        }
        form = ChangePasswordForm(user.user, data=form_data)
        self.assertFalse(form.is_valid())

        # 2. If passwords are too shorts
        form_data = {
            'password_old': 'hostel77',
            'password_new': 'pass',
            'password_confirm': 'pass'
        }
        form = ChangePasswordForm(user.user, data=form_data)
        self.assertFalse(form.is_valid())

        # 3. If passwords are equal to username
        form_data = {
            'password_old': 'hostel77',
            'password_new': user.user.username,
            'password_confirm': user.user.username
        }
        form = ChangePasswordForm(user.user, data=form_data)
        self.assertFalse(form.is_valid())
        
        # 4. If old password is wrong
        form_data = {
            'password_old': 'WrongPassword',
            'password_new': 'ThePassword1234',
            'password_confirm': 'ThePassword1234'
        }
        form = ChangePasswordForm(user.user, data=form_data)
        self.assertFalse(form.is_valid())
        
        # 5. If everything is OK
        form_data = {
            'password_old': 'hostel77',
            'password_new': 'ThePassword1234',
            'password_confirm': 'ThePassword1234'
        }
        form = ChangePasswordForm(user.user, data=form_data)
        self.assertTrue(form.is_valid())

    def test_update_profil(self):
        """Test the profil update (pseudo, email)"""
        
        # create dummy user (reference)
        user_ref = ProfileFactory()
        login_check = self.client.login(
            username=user_ref.user.username,
            password='hostel77')
        self.assertTrue(login_check)
        
        # create dummy user (to test)
        user = ProfileFactory()
        login_check = self.client.login(
            username=user.user.username,
            password='hostel77')
        self.assertTrue(login_check)
        
        # A. Test email update ----
        
        # A1. If email looks bad
        form_data = {
            'email_new': 'weirdemail@'
        }
        form = ChangeUserForm(data=form_data)
        self.assertFalse(form.is_valid())
        
        # A2. If email is taken
        form_data = {
            'email_new': user_ref.user.email
        }
        form = ChangeUserForm(data=form_data)
        self.assertFalse(form.is_valid())
        
        # A3. If email provider is forbidden
        form_data = {
            'email_new': 'dummy@yopmail.com'
        }
        form = ChangeUserForm(data=form_data)
        self.assertFalse(form.is_valid())
        
        # A4. If OK
        form_data = {
            'email_new': 'okmail@test.com'
        }
        form = ChangeUserForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        # B. t*Test pseudo update ---
        
        # B1. If new pseudo is taken
        form_data = {
            'username_new': user_ref.user.username
        }
        form = ChangeUserForm(data=form_data)
        self.assertFalse(form.is_valid())
        
        # B2. If new pseudo is OK
        form_data = {
            'username_new': 'OriginalPseudo'
        }
        form = ChangeUserForm(data=form_data)
        self.assertTrue(form.is_valid())
        
