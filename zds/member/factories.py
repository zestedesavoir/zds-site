import factory

from django.contrib.auth.models import User, Permission, Group
from django.conf import settings

from zds.member.models import Profile
from zds.utils.models import Hat


class UserFactory(factory.DjangoModelFactory):
    """
    This factory creates User.
    WARNING: Don't try to directly use `UserFactory`, this didn't create associated Profile then don't work!
    Use `ProfileFactory` instead.
    """
    class Meta:
        model = User

    username = factory.Sequence('firm{0}'.format)
    email = factory.Sequence('firm{0}@zestedesavoir.com'.format)
    password = 'hostel77'

    is_active = True

    @classmethod
    def _prepare(cls, create, **kwargs):
        password = kwargs.pop('password', None)
        user = super(UserFactory, cls)._prepare(create, **kwargs)
        if password:
            user.set_password(password)
            if create:
                user.save()
        return user


class StaffFactory(factory.DjangoModelFactory):
    """
    This factory creates staff User.
    WARNING: Don't try to directly use `StaffFactory`, this didn't create associated Profile then don't work!
    Use `StaffProfileFactory` instead.
    """
    class Meta:
        model = User

    username = factory.Sequence('firmstaff{0}'.format)
    email = factory.Sequence('firmstaff{0}@zestedesavoir.com'.format)
    password = 'hostel77'

    is_active = True

    @classmethod
    def _prepare(cls, create, **kwargs):
        password = kwargs.pop('password', None)
        user = super(StaffFactory, cls)._prepare(create, **kwargs)
        if password:
            user.set_password(password)
            if create:
                user.save()
        group_staff = Group.objects.filter(name='staff').first()
        if group_staff is None:
            group_staff = Group(name='staff')
            group_staff.save()
            hat, _ = Hat.objects.get_or_create(name__iexact='Staff', defaults={'name': 'Staff'})
            hat.group = group_staff
            hat.save()

        perms = Permission.objects.filter(codename__startswith='change_').all()
        group_staff.permissions = perms
        user.groups.add(group_staff)

        user.save()
        return user


class DevFactory(factory.DjangoModelFactory):
    """
    This factory creates dev User.
    WARNING: Don't try to directly use `DevFactory`, this didn't create associated Profile then don't work!
    Use `DevProfileFactory` instead.
    """
    class Meta:
        model = User

    username = factory.Sequence('firmdev{0}'.format)
    email = factory.Sequence('firmdev{0}@zestedesavoir.com'.format)
    password = 'hostel77'

    is_active = True

    @classmethod
    def _prepare(cls, create, **kwargs):
        password = kwargs.pop('password', None)
        user = super(DevFactory, cls)._prepare(create, **kwargs)
        if password:
            user.set_password(password)
            if create:
                user.save()
        group_dev = Group.objects.filter(name=settings.ZDS_APP['member']['dev_group']).first()
        if group_dev is None:
            group_dev = Group(name=settings.ZDS_APP['member']['dev_group'])
            group_dev.save()

        user.groups.add(group_dev)

        user.save()
        return user


class ProfileFactory(factory.DjangoModelFactory):
    """
    Use this factory when you need a complete Profile for a standard user.
    """
    class Meta:
        model = Profile

    user = factory.SubFactory(UserFactory)

    last_ip_address = '192.168.2.1'
    site = 'www.zestedesavoir.com'

    @factory.lazy_attribute
    def biography(self):
        return 'My name is {0} and I i\'m the guy who kill the bad guys '.format(self.user.username.lower())

    sign = 'Please look my flavour'


class ProfileNotSyncFactory(ProfileFactory):
    """
    Use this factory when you want a user with wrong identifiers.
    """
    id = factory.Sequence(lambda n: n + 99999)


class StaffProfileFactory(factory.DjangoModelFactory):
    """
    Use this factory when you need a complete Profile for a staff user.
    """
    class Meta:
        model = Profile

    user = factory.SubFactory(StaffFactory)

    last_ip_address = '192.168.2.1'
    site = 'www.zestedesavoir.com'

    @factory.lazy_attribute
    def biography(self):
        return 'My name is {0} and I i\'m the guy who kill the bad guys '.format(self.user.username.lower())

    sign = 'Please look my flavour'


class DevProfileFactory(factory.DjangoModelFactory):
    """
    Use this factory when you need a complete Profile for a dev user.
    """
    class Meta:
        model = Profile

    user = factory.SubFactory(DevFactory)

    last_ip_address = '192.168.2.1'
    site = 'www.zestedesavoir.com'

    @factory.lazy_attribute
    def biography(self):
        return 'My name is {0} and I i\'m the guy who kill the bad guys '.format(self.user.username.lower())

    sign = 'Please look my flavour'


class NonAsciiUserFactory(UserFactory):
    """
    This factory creates standard user with non-ASCII characters in its username.
    WARNING: Don't try to directly use `NonAsciiUserFactory`, this didn't create associated Profile then don't work!
    Use `NonAsciiProfileFactory` instead.
    """
    class Meta:
        model = User

    username = factory.Sequence('ïéàçÊÀ{0}'.format)


class NonAsciiProfileFactory(ProfileFactory):
    """
    Use this factory to create a standard user with non-ASCII characters in its username.
    """
    class Meta:
        model = Profile

    user = factory.SubFactory(NonAsciiUserFactory)
