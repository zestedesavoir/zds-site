from django.conf import settings
from zds.member.decorator import LoggedWithReadWriteHability
from zds.tutorialv2.mixins import SingleContentDetailViewMixin
from zds.tutorialv2.models.events import Event
from zds.utils.paginator import make_pagination


class EventList(LoggedWithReadWriteHability, SingleContentDetailViewMixin):
    """
    Display contact page.
    """

    model = Event
    template_name = "tutorialv2/view/events.html"

    def get_context_data(self, **kwargs):
        context = super(EventList, self).get_context_data(**kwargs)
        events = list(Event.objects.filter(content=self.object))
        events.reverse()
        make_pagination(
            context, self.request, events, settings.ZDS_APP["content"]["commits_per_page"], context_list_name="events"
        )
        return context
