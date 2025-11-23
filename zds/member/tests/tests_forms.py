from django.test import TestCase

from zds.member.forms import (
    ChangePasswordForm,
    ChangeUserForm,
    KarmaForm,
    MiniProfileForm,
    NewPasswordForm,
    ProfileForm,
    RegisterForm,
    UnregisterForm,
    UsernameAndEmailForm,
)
from zds.member.models import BannedEmailProvider
from zds.member.tests.factories import NonAsciiProfileFactory, ProfileFactory, StaffProfileFactory

stringof77chars = "abcdefghijklmnopqrstuvwxyz0123456789abcdefghijklmnopqrstuvwxyz0123456789-----"
stringof251chars = (
    "abcdefghijklmnopqrstuvwxyabcdefghijklmnopqrstuvwxy"
    "abcdefghijklmnopqrstuvwxyabcdefghijklmnopqrstuvwxy"
    "abcdefghijklmnopqrstuvwxyabcdefghijklmnopqrstuvwxy"
    "abcdefghijklmnopqrstuvwxyabcdefghijklmnopqrstuvwxy"
    "abcdefghijklmnopqrstuvwxyabcdefghijklmnopqrstuvwxy0"
)
stringof501chars = ["1" for n in range(501)]
stringof2001chars = "http://url.com/"
for i in range(198):
    stringof2001chars += "0123456789"
stringof2001chars += "12.jpg"


class RegisterFormTest(TestCase):
    """
    Check the registering form.
    """

    def test_valid_register_form(self):
        data = {
            "email": "test@gmail.com",
            "username": "ZeTester",
            "password": "ZePassword",
            "password_confirm": "ZePassword",
        }
        form = RegisterForm(data=data)
        self.assertTrue(form.is_valid())

    def test_empty_email_register_form(self):
        data = {"email": "", "username": "ZeTester", "password": "ZePassword", "password_confirm": "ZePassword"}
        form = RegisterForm(data=data)
        self.assertFalse(form.is_valid())

    def test_empty_username_register_form(self):
        data = {"email": "test@gmail.com", "username": "", "password": "ZePassword", "password_confirm": "ZePassword"}
        form = RegisterForm(data=data)
        self.assertFalse(form.is_valid())

    def test_utf8mb4_username_register_form(self):
        data = {"email": "test@gmail.com", "username": "🐙", "password": "ZePassword", "password_confirm": "ZePassword"}
        form = RegisterForm(data=data)
        self.assertFalse(form.is_valid())

    def test_empty_spaces_username_register_form(self):
        data = {
            "email": "test@gmail.com",
            "username": "   ",
            "password": "ZePassword",
            "password_confirm": "ZePassword",
        }
        form = RegisterForm(data=data)
        self.assertFalse(form.is_valid())

    def test_forbidden_email_provider_register_form(self):
        moderator = StaffProfileFactory().user
        if not BannedEmailProvider.objects.filter(provider="yopmail.com").exists():
            BannedEmailProvider.objects.create(provider="yopmail.com", moderator=moderator)
        data = {
            "email": "test@yopmail.com",
            "username": "ZeTester",
            "password": "ZePassword",
            "password_confirm": "ZePassword",
        }
        form = RegisterForm(data=data)
        self.assertFalse(form.is_valid())

    def test_not_matching_password_register_form(self):
        data = {
            "email": "test@gmail.com",
            "username": "ZeTester",
            "password": "ZePass",
            "password_confirm": "ZePassword",
        }
        form = RegisterForm(data=data)
        self.assertFalse(form.is_valid())

    def test_too_short_password_register_form(self):
        data = {"email": "test@gmail.com", "username": "ZeTester", "password": "pass", "password_confirm": "pass"}
        form = RegisterForm(data=data)
        self.assertFalse(form.is_valid())

    def test_password_match_username_password_register_form(self):
        data = {
            "email": "test@gmail.com",
            "username": "ZeTester",
            "password": "ZeTester",
            "password_confirm": "ZeTester",
        }
        form = RegisterForm(data=data)
        self.assertFalse(form.is_valid())

    def test_username_exist_register_form(self):
        testuser = ProfileFactory()
        data = {
            "email": "test@gmail.com",
            "username": testuser.user.username,
            "password": "ZeTester",
            "password_confirm": "ZeTester",
        }
        form = RegisterForm(data=data)
        self.assertFalse(form.is_valid())

    def test_email_exist_register_form(self):
        testuser = ProfileFactory()
        data = {
            "email": testuser.user.email,
            "username": "ZeTester",
            "password": "ZeTester",
            "password_confirm": "ZeTester",
        }
        form = RegisterForm(data=data)
        self.assertFalse(form.is_valid())

    def test_username_spaces_register_form(self):
        ProfileFactory()
        data = {
            "email": "test@gmail.com",
            "username": "  ZeTester  ",
            "password": "ZePassword",
            "password_confirm": "ZePassword",
        }
        form = RegisterForm(data=data)
        self.assertFalse(form.is_valid())

    def test_username_coma_register_form(self):
        ProfileFactory()
        data = {
            "email": "test@gmail.com",
            "username": "Ze,Tester",
            "password": "ZePassword",
            "password_confirm": "ZePassword",
        }
        form = RegisterForm(data=data)
        self.assertFalse(form.is_valid())

    def test_username_slash_register_form(self):
        ProfileFactory()
        data = {
            "email": "test@gmail.com",
            "username": "Ze/Tester",
            "password": "ZePassword",
            "password_confirm": "ZePassword",
        }
        form = RegisterForm(data=data)
        self.assertFalse(form.is_valid())

    def test_username_character_null(self):
        ProfileFactory()
        data = {
            "email": "test@gmail.com",
            "username": "foo\x00bar",
            "password": "ZePassword",
            "password_confirm": "ZePassword",
        }
        form = RegisterForm(data=data)
        self.assertFalse(form.is_valid())


class UnregisterFormTest(TestCase):
    """
    Check the unregistering form.
    """

    def setUp(self):
        self.user1 = ProfileFactory()

    def test_password_is_required(self):
        data = {}
        form = UnregisterForm(data=data, user=self.user1.user)
        self.assertFalse(form.is_valid())
        self.assertIn("password", form.errors.keys())


class MiniProfileFormTest(TestCase):
    """
    Check the miniprofile form.
    """

    def setUp(self):
        self.user1 = ProfileFactory()

    def test_valid_change_miniprofile_form(self):
        data = {"biography": "", "site": "", "avatar_url": "", "sign": ""}
        form = MiniProfileForm(data=data)
        self.assertTrue(form.is_valid())

    def test_site_url_without_protocol_miniprofile_form(self):
        data = {"biography": "", "site": "www.airbus.com", "avatar_url": "", "sign": ""}
        form = MiniProfileForm(data=data)
        self.assertTrue(form.is_valid())

    def test_site_url_with_bad_protocol_miniprofile_form(self):
        data = {"biography": "", "site": "avion://www.airbus.com", "avatar_url": "", "sign": ""}
        form = MiniProfileForm(data=data)
        self.assertFalse(form.is_valid())

    def test_site_url_with_http_protocol_miniprofile_form(self):
        data = {"biography": "", "site": "https://www.airbus.com", "avatar_url": "", "sign": ""}
        form = MiniProfileForm(data=data)
        self.assertTrue(form.is_valid())

    def test_site_url_with_https_protocol_miniprofile_form(self):
        data = {"biography": "", "site": "https://www.airbus.com", "avatar_url": "", "sign": ""}
        form = MiniProfileForm(data=data)
        self.assertTrue(form.is_valid())

    def test_too_long_site_url_miniprofile_form(self):
        # url is one char too long
        data = {"biography": "", "site": stringof2001chars, "avatar_url": "", "sign": ""}
        form = MiniProfileForm(data=data)
        self.assertFalse(form.is_valid())

    def test_too_long_avatar_url_miniprofile_form(self):
        data = {"biography": "", "site": "", "avatar_url": stringof2001chars, "sign": ""}
        form = MiniProfileForm(data=data)
        self.assertFalse(form.is_valid())

    def test_too_long_signature_miniprofile_form(self):
        data = {"biography": "", "site": "", "avatar_url": "", "sign": stringof501chars}
        form = MiniProfileForm(data=data)
        self.assertFalse(form.is_valid())


class ProfileFormTest(TestCase):
    """
    Check the form is working (and that's all).
    """

    def test_valid_profile_form(self):
        data = {}
        form = ProfileForm(data=data)
        self.assertTrue(form.is_valid())


class ChangeUserFormTest(TestCase):
    """
    Check the user username/email.
    """

    def setUp(self):
        self.user1 = ProfileFactory()
        self.user2 = ProfileFactory()

    def test_valid_change_username_user_form(self):
        data = {"username": "MyNewPseudo", "email": self.user1.user.email, "password": "hostel77"}
        form = ChangeUserForm(data=data, user=self.user1.user)
        self.assertTrue(form.is_valid())

    def test_valid_change_email_user_form(self):
        data = {"username": self.user1.user.username, "email": "test@gmail.com", "password": "hostel77"}
        form = ChangeUserForm(data=data, user=self.user1.user)
        self.assertTrue(form.is_valid())

    def test_already_used_username_user_form(self):
        data = {"username": self.user2.user.username, "email": self.user1.user.email, "password": "hostel77"}
        form = ChangeUserForm(data=data, user=self.user1.user)
        self.assertFalse(form.is_valid())

    def test_already_used_email_user_form(self):
        data = {"username": self.user1.user.username, "email": self.user2.user.email, "password": "hostel77"}
        form = ChangeUserForm(data=data, user=self.user1.user)
        self.assertFalse(form.is_valid())

    def test_forbidden_email_provider_user_form(self):
        moderator = StaffProfileFactory().user
        if not BannedEmailProvider.objects.filter(provider="yopmail.com").exists():
            BannedEmailProvider.objects.create(provider="yopmail.com", moderator=moderator)
        data = {"username": self.user1.user.username, "email": "test@yopmail.com", "password": "hostel77"}
        form = ChangeUserForm(data=data, user=self.user1.user)
        self.assertFalse(form.is_valid())

    def test_wrong_email_user_form(self):
        data = {"username": self.user1.user.username, "email": "wrong@", "password": "hostel77"}
        form = ChangeUserForm(data=data, user=self.user1.user)
        self.assertFalse(form.is_valid())

        data = {"username": self.user1.user.username, "email": "@test.com", "password": "hostel77"}
        form = ChangeUserForm(data=data, user=self.user1.user)
        self.assertFalse(form.is_valid())

        data = {"username": self.user1.user.username, "email": "wrong@test", "password": "hostel77"}
        form = ChangeUserForm(data=data, user=self.user1.user)
        self.assertFalse(form.is_valid())

        data = {"username": self.user1.user.username, "email": "wrong@.com", "password": "hostel77"}
        form = ChangeUserForm(data=data, user=self.user1.user)
        self.assertFalse(form.is_valid())

        data = {"username": self.user1.user.username, "email": "wrongtest.com", "password": "hostel77"}
        form = ChangeUserForm(data=data, user=self.user1.user)
        self.assertFalse(form.is_valid())

    def test_username_spaces_register_form(self):
        ProfileFactory()
        data = {
            "username": "  ZeTester  ",
            "password": "hostel77",
            "email": self.user1.user.email,
        }
        form = ChangeUserForm(data=data, user=self.user1.user)
        self.assertFalse(form.is_valid())

    def test_username_coma_register_form(self):
        ProfileFactory()
        data = {
            "username": "Ze,Tester",
            "password": "hostel77",
            "email": self.user1.user.email,
        }
        form = ChangeUserForm(data=data, user=self.user1.user)
        self.assertFalse(form.is_valid())

    def test_username_slash_changeuser_form(self):
        ProfileFactory()
        data = {
            "username": "Ze/Tester",
            "password": "hostel77",
            "email": self.user1.user.email,
        }
        form = ChangeUserForm(data=data, user=self.user1.user)
        self.assertFalse(form.is_valid())

    def test_password_is_required(self):
        ProfileFactory()
        data = {
            "username": "ZeTester",
            "email": self.user1.user.email,
        }
        form = ChangeUserForm(data=data, user=self.user1.user)
        self.assertFalse(form.is_valid())
        self.assertIn("password", form.errors.keys())


class ChangePasswordFormTest(TestCase):
    """
    Check the form to change the password.
    """

    def setUp(self):
        self.user1 = ProfileFactory()
        self.old_password = "hostel77"
        self.new_password = "TheNewPassword"

    def test_valid_change_password_form(self):
        data = {
            "password": self.old_password,
            "password_new": self.new_password,
            "password_confirm": self.new_password,
        }
        form = ChangePasswordForm(data=data, user=self.user1.user)
        self.assertTrue(form.is_valid())

    def test_old_wrong_change_password_form(self):
        data = {"password": "Wronnnng", "password_new": self.new_password, "password_confirm": self.new_password}
        form = ChangePasswordForm(data=data, user=self.user1.user)
        self.assertFalse(form.is_valid())

    def test_not_matching_change_password_form(self):
        data = {"password": self.old_password, "password_new": self.new_password, "password_confirm": "Wronnnng"}
        form = ChangePasswordForm(data=data, user=self.user1.user)
        self.assertFalse(form.is_valid())

    def test_too_short_change_password_form(self):
        too_short = "short"
        data = {"password": self.old_password, "password_new": too_short, "password_confirm": too_short}
        form = ChangePasswordForm(data=data, user=self.user1.user)
        self.assertFalse(form.is_valid())

    def test_match_username_change_password_form(self):
        self.user1.user.username = "LongName"
        data = {
            "password": self.old_password,
            "password_new": self.user1.user.username,
            "password_confirm": self.user1.user.username,
        }
        form = ChangePasswordForm(data=data, user=self.user1.user)
        self.assertFalse(form.is_valid())


class UsernameAndEmailFormTest(TestCase):
    """
    Check the form to ask for a new password.
    """

    def setUp(self):
        self.user1 = ProfileFactory()
        self.userNonAscii = NonAsciiProfileFactory()

    def test_valid_forgot_password_form(self):
        data = {"username": self.user1.user.username, "email": ""}
        form = UsernameAndEmailForm(data=data)
        self.assertTrue(form.is_valid())

    def test_non_valid_non_ascii_forgot_password_form(self):
        data = {"username": self.userNonAscii.user.username, "email": ""}
        form = UsernameAndEmailForm(data=data)
        self.assertTrue(form.is_valid())

    def test_non_valid_non_ascii_email_forgot_password_form(self):
        data = {"username": "", "email": self.userNonAscii.user.email}
        form = UsernameAndEmailForm(data=data)
        self.assertTrue(form.is_valid())

    def test_valid_email_forgot_password_form(self):
        data = {"email": self.user1.user.email, "username": ""}
        form = UsernameAndEmailForm(data=data)
        self.assertTrue(form.is_valid())

    def test_empty_name_forgot_password_form(self):
        data = {"username": "", "email": ""}
        form = UsernameAndEmailForm(data=data)
        self.assertFalse(form.is_valid())

    def test_full_forgot_password_form(self):
        data = {"username": "John Doe", "email": "john.doe@gmail.com"}
        form = UsernameAndEmailForm(data=data)
        self.assertFalse(form.is_valid())

    def test_unknow_username_forgot_password_form(self):
        data = {"username": "John Doe", "email": ""}
        form = UsernameAndEmailForm(data=data)
        self.assertFalse(form.is_valid())

    def test_unknow_email_forgot_password_form(self):
        data = {"email": "john.doe@gmail.com", "username": ""}
        form = UsernameAndEmailForm(data=data)
        self.assertFalse(form.is_valid())


class NewPasswordFormTest(TestCase):
    """
    Check the form to input the new password.
    """

    def setUp(self):
        self.user1 = ProfileFactory()
        self.newpassword = "TheNewPassword"

    def test_valid_new_password_form(self):
        data = {"password": self.newpassword, "password_confirm": self.newpassword}
        form = NewPasswordForm(data=data, identifier=self.user1.user.username)
        self.assertTrue(form.is_valid())

    def test_not_matching_new_password_form(self):
        data = {"password": self.newpassword, "password_confirm": "Wronnngggg"}
        form = NewPasswordForm(data=data, identifier=self.user1.user.username)
        self.assertFalse(form.is_valid())

    def test_password_is_username_new_password_form(self):
        data = {"password": self.user1.user.username, "password_confirm": self.user1.user.username}
        form = NewPasswordForm(data=data, identifier=self.user1.user.username)
        self.assertFalse(form.is_valid())

    def test_password_too_short_new_password_form(self):
        too_short = "short"
        data = {"password": too_short, "password_confirm": too_short}
        form = NewPasswordForm(data=data, identifier=self.user1.user.username)
        self.assertFalse(form.is_valid())


class KarmaFormTest(TestCase):
    """
    Check the form to impact the karma of a user.
    """

    def setUp(self):
        self.user = ProfileFactory()

    def test_valid_karma_form(self):
        data = {"note": "bad user is bad !", "karma": "-50"}
        form = KarmaForm(data=data, profile=self.user)
        self.assertTrue(form.is_valid())

    def test_missing_warning_karma_form(self):
        data = {"note": "", "karma": "-50"}
        form = KarmaForm(data=data, profile=self.user)
        self.assertFalse(form.is_valid())

    def test_missing_points_karma_form(self):
        data = {"note": "bad user is bad !", "karma": ""}
        form = KarmaForm(data=data, profile=self.user)
        # should be fine as points is not required=True
        self.assertTrue(form.is_valid())
