from django.contrib.auth.models import Group
from django.test import TestCase

from zds.forum.tests.factories import create_category_and_forum
from zds.forum.utils import get_authorized_forums_pk
from zds.member.tests.factories import ProfileFactory, StaffProfileFactory


class GetAuthorizedForumsTests(TestCase):
    def test_get_authorized_forums_pk(self):
        user = ProfileFactory().user
        staff = StaffProfileFactory().user

        # 1. Create a hidden forum belonging to a hidden staff group:
        group = Group.objects.create(name="Les illuminatis anonymes de ZdS")
        _, hidden_forum = create_category_and_forum(group)

        staff.groups.add(group)
        staff.save()

        # 2. Create a public forum:
        _, public_forum = create_category_and_forum()

        # 3. Regular user can access only the public forum:
        self.assertEqual(get_authorized_forums_pk(user), [public_forum.pk])

        # 4. Staff user can access all forums:
        self.assertEqual(sorted(get_authorized_forums_pk(staff)), sorted([hidden_forum.pk, public_forum.pk]))

        # 5. By default, only public forums are available:
        self.assertEqual(get_authorized_forums_pk(None), [public_forum.pk])
