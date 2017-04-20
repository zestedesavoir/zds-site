from django.test import TestCase

from zds.utils.templatetags.profile import state
from zds.member.factories import ProfileFactory


class ProfileTest(TestCase):
    def test_staff_badge(self):
        user = ProfileFactory()

        self.assertEqual(None, state(user.user))

        result = self.client.get(
            user.get_absolute_url(),
            follow=False
        )
        self.assertEqual(200, result.status_code)
        self.assertNotContains(result, 'Staff')

        # Make the user superuser to give him the staff perms
        user.user.is_superuser = True
        user.user.save()

        self.assertEqual('STAFF', state(user.user))

        result = self.client.get(
            user.get_absolute_url(),
            follow=False
        )
        self.assertEqual(200, result.status_code)
        self.assertContains(result, 'Staff')
