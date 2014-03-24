from django.contrib.auth.models import User, Permission
import factory

from zds.member.models import Profile


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

class StaffFactory(factory.DjangoModelFactory):
    FACTORY_FOR = User
    
    username = factory.Sequence(lambda n: 'firmstaff{0}'.format(n))
    email = factory.Sequence(lambda n: 'firmstaff{0}@zestedesavoir.com'.format(n))
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
        user.user_permissions.add(Permission.objects.get(codename='moderation'))
        user.user_permissions.add(Permission.objects.get(codename='show_ip'))
        
        user.save()
        return user
    
class ProfileFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Profile
    
    last_ip_address = '192.168.2.1'
    site = 'www.zestedesavoir.com'
    biography = factory.LazyAttribute(lambda a:'My name is {0} and I i\'m the guy who kill the bad guys '.format(a.username.lower()))
    sign = 'Please look my flavour'
    
    @classmethod
    def _prepare(cls, create, **kwargs):
        user = kwargs.pop('user', None)
        profile = super(ProfileFactory, cls)._prepare(create, **kwargs)
        if user:
            profile.user = user
            profile.save()
        
        return profile
