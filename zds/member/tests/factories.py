import factory

from django.contrib.auth.models import User, Permission, Group
from django.conf import settings

from zds.member.models import Profile
from zds.utils.models import Hat


class UserFactory(factory.django.DjangoModelFactory):
    """
    Factory that creates a standard User.

    WARNING: Don't try to directly use `UserFactory` because it won't create the associated Profile.
    Use `ProfileFactory` instead.
    """

    class Meta:
        model = User

    username = factory.Sequence("firm{}".format)
    email = factory.Sequence("firm{}@zestedesavoir.com".format)
    password = factory.PostGenerationMethodCall("set_password", "hostel77")

    is_active = True


class StaffFactory(UserFactory):
    """
    Factory that creates a Staff User (within the Staff group and with change_* permissions).

    WARNING: Don't try to directly use `StaffFactory` because it won't create the associated Profile.
    Use `StaffProfileFactory` instead.
    """

    username = factory.Sequence("firmstaff{}".format)
    email = factory.Sequence("firmstaff{}@zestedesavoir.com".format)

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        group_staff = Group.objects.filter(name="staff").first()

        if group_staff is None:
            group_staff = Group(name="staff")
            group_staff.save()
            hat, _ = Hat.objects.get_or_create(name__iexact="Staff", defaults={"name": "Staff"})
            hat.group = group_staff
            hat.save()

        perms = Permission.objects.filter(codename__startswith="change_").all()
        for perm in perms:
            group_staff.permissions.add(perm)

        self.groups.add(group_staff)


class DevFactory(UserFactory):
    """
    Factory that creates a Dev User (within the Dev group).

    WARNING: Don't try to directly use `DevFactory` because it won't create the associated Profile.
    Use `DevProfileFactory` instead.
    """

    username = factory.Sequence("firmdev{}".format)
    email = factory.Sequence("firmdev{}@zestedesavoir.com".format)

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        group_dev = Group.objects.filter(name=settings.ZDS_APP["member"]["dev_group"]).first()

        if group_dev is None:
            group_dev = Group(name=settings.ZDS_APP["member"]["dev_group"])
            group_dev.save()

        self.groups.add(group_dev)


class NonAsciiUserFactory(UserFactory):
    """
    Factory that creates a User with non-ASCII characters in their username.

    WARNING: Don't try to directly use `NonAsciiUserFactory` because it won't create the associated Profile.
    Use `NonAsciiProfileFactory` instead.
    """

    username = factory.Sequence("ïéàçÊÀ{}".format)


class ProfileFactory(factory.django.DjangoModelFactory):
    """
    Use this factory when you need a complete Profile for a standard User.
    """

    class Meta:
        model = Profile

    user = factory.SubFactory(UserFactory)

    last_ip_address = "192.168.2.1"
    site = "www.zestedesavoir.com"

    @factory.lazy_attribute
    def biography(self):
        return f"My name is {self.user.username.lower()} and I i'm the guy who kill the bad guys "

    sign = "Please look my flavour"


class ProfileNotSyncFactory(ProfileFactory):
    """
    Use this factory when you need a complete Profile for a User with wrong identifiers.
    """

    id = factory.Sequence(lambda n: n + 99999)


class StaffProfileFactory(ProfileFactory):
    """
    Use this factory when you need a complete Profile for a Staff User.
    """

    user = factory.SubFactory(StaffFactory)


class DevProfileFactory(ProfileFactory):
    """
    Use this factory when you need a complete Profile for a Dev User.
    """

    user = factory.SubFactory(DevFactory)


class NonAsciiProfileFactory(ProfileFactory):
    """
    Use this factory when you need a complete Profile for a User with non-ASCII characters in their username.
    """

    user = factory.SubFactory(NonAsciiUserFactory)
