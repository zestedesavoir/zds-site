from django.apps import AppConfig
from django.conf import settings
from django.contrib.auth import get_user_model

class MemberConfig(AppConfig):
    name = 'zds.member'

    def ready(self):
        # Imported here cause apps aren't loaded yet.
        User = get_user_model()

        for user in ('bot_account', 'anonymous_account', 'external_account'):
            username = settings.ZDS_APP['member'][user]
            try:
                test = User.objects.get(username=username)
            except User.DoesNotExist:
                raise Exception(
                    'The {username!r} user does not exist. '
                    'You must create it to run the server.'.format(
                        username=username
                    )
                )
