from django.contrib.auth.models import User, Permission
import factory

from zds.member.models import Profile

# Don't try to directly use UserFactory, this didn't create Profile then don't work!
class UserFactory(factory.DjangoModelFactory):
    FACTORY_FOR = User

    username = factory.Sequence(lambda n: 'firm{0}'.format(n))
    email = factory.Sequence(lambda n: 'firm{0}@zestedesavoir.com'.format(n))
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

# Don't try to directly use StaffFactory, this didn't create Profile then don't work!
class StaffFactory(factory.DjangoModelFactory):
    FACTORY_FOR = User

    username = factory.Sequence(lambda n: 'firmstaff{0}'.format(n))
    email = factory.Sequence(
        lambda n: 'firmstaff{0}@zestedesavoir.com'.format(n))
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
        perms = Permission.objects.filter(codename__startswith='change_').all()

        user.user_permissions = list(perms)
        user.user_permissions.add(
            Permission.objects.get(
                codename='moderation'))
        user.user_permissions.add(Permission.objects.get(codename='show_ip'))

        user.save()
        return user


class ProfileFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Profile

    user = factory.SubFactory(UserFactory)

    last_ip_address = '192.168.2.1'
    site = 'www.zestedesavoir.com'

    @factory.lazy_attribute
    def biography(self):
        return 'My name is {0} and I i\'m the guy who kill the bad guys '.format(
            self.user.username.lower())

    sign = 'Please look my flavour'
    

class StaffProfileFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Profile

    user = factory.SubFactory(StaffFactory)

    last_ip_address = '192.168.2.1'
    site = 'www.zestedesavoir.com'

    @factory.lazy_attribute
    def biography(self):
        return 'My name is {0} and I i\'m the guy who kill the bad guys '.format(
            self.user.username.lower())

    sign = 'Please look my flavour'
