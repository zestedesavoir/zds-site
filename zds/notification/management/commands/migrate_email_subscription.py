from django.core.management import BaseCommand

from zds.member.models import Profile
from zds.notification.models import TopicAnswerSubscription, TopicFollowed


class Command(BaseCommand):
    help = "Migrate old email subscriptions to new models."

    def handle(self, *args, **options):
        for profile in Profile.objects.all():
            self.stdout.write(f"Starting migration for {profile.user.username}")

            # Get alls topic followed by the user.
            topics_followed = (
                TopicFollowed.objects.filter(user=profile.user, email=True).values("topic").distinct().all()
            )

            # And update email attribute in the TopicAnswerSubscription model.
            for topic in topics_followed:
                active = TopicAnswerSubscription.objects.get_or_create_active(user=profile.user, content_object=topic)
                active.email = True
                active.save()
