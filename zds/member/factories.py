# coding: utf-8

from django.contrib.auth.models import User, Permission, Group
import factory

from zds.member.models import Profile


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
        group_staff = Group.objects.filter(name="staff").first()
        if group_staff is None:
            group_staff = Group(name="staff")
            group_staff.save()

        perms = Permission.objects.filter(codename__startswith='change_').all()
        group_staff.permissions = perms
        user.groups.add(group_staff)

        user.save()
        return user


class AdminFactory(factory.DjangoModelFactory):
    """
    This factory creates admin User.
    WARNING: Don't try to directly use `AdminFactory`, this didn't create associated Profile then don't work!
    Use `AdminProfileFactory` instead.
    """
    class Meta:
        model = User

    username = factory.Sequence('admin{0}'.format)
    email = factory.Sequence('firmstaff{0}@zestedesavoir.com'.format)
    password = 'hostel77'
    
    is_superuser = True
    is_staff = True
    is_active = True
    
    @classmethod
    def _prepare(cls, create, **kwargs):
        password = kwargs.pop('password', None)
        user = super(AdminFactory, cls)._prepare(create, **kwargs)
        if password:
            user.set_password(password)
            if create:
                user.save()
        group_staff = Group.objects.filter(name="staff").first()
        if group_staff is None:
            group_staff = Group(name="staff")
            group_staff.save()

        perms = Permission.objects.all()
        group_staff.permissions = perms
        user.groups.add(group_staff)

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
        return u'My name is {0} and I i\'m the guy who kill the bad guys '.format(self.user.username.lower())

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
        return u'My name is {0} and I i\'m the guy who kill the bad guys '.format(self.user.username.lower())

    sign = 'Please look my flavour'


class AdminProfileFactory(factory.DjangoModelFactory):
    """
    Use this factory when you need a complete admin Profile for a user.
    """
    class Meta:
        model = Profile

    user = factory.SubFactory(AdminFactory)

    last_ip_address = '192.168.2.1'
    site = 'www.zestedesavoir.com'

    @factory.lazy_attribute
    def biography(self):
        return u'My name is {0} and I i\'m the guy who control the guy that kill the bad guys '.format(self.user.username.lower())

    sign = 'Please look my flavour'


class NonAsciiUserFactory(UserFactory):
    """
    This factory creates standard user with non-ASCII characters in its username.
    WARNING: Don't try to directly use `NonAsciiUserFactory`, this didn't create associated Profile then don't work!
    Use `NonAsciiProfileFactory` instead.
    """
    class Meta:
        model = User

    username = factory.Sequence(u'ïéàçÊÀ{0}'.format)


class NonAsciiProfileFactory(ProfileFactory):
    """
    Use this factory to create a standard user with non-ASCII characters in its username.
    """
    class Meta:
        model = Profile

    user = factory.SubFactory(NonAsciiUserFactory)
