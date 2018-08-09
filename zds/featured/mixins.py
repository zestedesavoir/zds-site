from zds.featured.models import FeaturedRequested
from django.views.generic.base import ContextMixin, View


class FeatureableMixin(ContextMixin,View):
    """Mixin for object that may be featured

    To be used with ``SingleObjectMixin`` or derived.
    """

    def toogle_featured_request(self, user=None):
        return FeaturedRequested.objects.toogle_request(self.object, user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['show_featured_requested'] = True
        context['is_requesting'], context['featured_request_count'] = FeaturedRequested.objects.requested_and_count(
            self.object, self.request.user)

        return context
