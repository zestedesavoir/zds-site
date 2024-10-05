from hashlib import md5
from time import sleep

import requests
from django.core.management.base import BaseCommand
from django.db.models import Q

from zds.member.models import Profile


class Command(BaseCommand):
    help = "Migrate from Gravatar"

    def handle(self, *args, **options):
        # We have profiles with either NULL or empty avatar_url field
        profiles_without_avatar_url = Profile.objects.filter(Q(avatar_url__isnull=True) | Q(avatar_url=""))
        total = profiles_without_avatar_url.count()
        i = 1
        for profile in profiles_without_avatar_url.iterator():
            hash = md5(profile.user.email.lower().encode("utf-8")).hexdigest()
            gravatar_url = f"https://secure.gravatar.com/avatar/{hash}"
            r = requests.get(f"{gravatar_url}?d=404")
            if r.status_code == 200:
                profile.avatar_url = f"{gravatar_url}?s=200"
                profile.save()
            self.stdout.write(f"\rProgress: {i}/{total}", ending="")
            i += 1
            sleep(1)
        self.stdout.write(self.style.SUCCESS("\nSuccessfully migrated from Gravatar!"))
