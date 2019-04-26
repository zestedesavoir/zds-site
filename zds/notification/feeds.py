from django.contrib.syndication.views import Feed
from django.http import HttpRequest, Http404
from django.utils.feedgenerator import Atom1Feed
from django.conf import settings
from django.utils.translation import gettext as _

from zds.member.models import Profile
from zds.notification.models import Notification


class MemberNotificationFeed(Feed):
    token = None
    description = _('Mes dernières notifications')

    def get_object(self, request: HttpRequest, *args, **kwargs):
        self.token = kwargs['token']
        return super().get_object(request, *args, **kwargs)

    def items(self):
        user = Profile.objects.filter(rss_token=self.token).prefetch_related('user').first()
        if not user:
            raise Http404('No user with ' + self.token)
        feed_length = settings.ZDS_APP['content']['feed_length']
        return Notification.objects.filter(subscription__user=user)[:feed_length]

    def item_title(self, item):
        return item.title

    def item_pubdate(self, item):
        return item.pubdate

    def item_description(self, item):
        return ''

    def item_author_name(self, item):
        return item.sender.username

    def item_link(self, item):
        return item.url


class MemberNotificationAtomFeed(MemberNotificationFeed):
    feed_type = Atom1Feed
    subtitle = MemberNotificationFeed.description
