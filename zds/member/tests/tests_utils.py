from unittest import TestCase

from zds.member.models import Profile


class MemberTests(TestCase):
    def test_find_username_skeleton(self):
        usernames = [
            {"username": "adr1", "skeleton": "adr1", "reason": "no special add"},
            {"username": "adr 1", "skeleton": "adr1", "reason": "add normal ascii space"},
            {"username": "adr 1", "skeleton": "adr1", "reason": "add space (U+00A0)"},
            {"username": "adr 1", "skeleton": "adr1", "reason": "add space (U+2004)"},
            {"username": "adr1", "skeleton": "adr1", "reason": "add space (U+00A0)"},
            {"username": "ХР123.", "skeleton": "xp123.", "reason": "cyrilic X and P"},
            {"username": "adr–1", "skeleton": "adr-1", "reason": "add U+2013"},
            {"username": "adr—1", "skeleton": "adr1", "reason": "add U+2014"},
        ]
        for username in usernames:
            name = Profile.find_username_skeleton(username["username"])
            skeleton = Profile.find_username_skeleton(username["skeleton"])
            self.assertEqual(
                name,
                skeleton,
                f"Username {username['username']} give unexpected skeleton "
                f"'{name}' instead of '{skeleton}' : {username['reason']}",
            )
