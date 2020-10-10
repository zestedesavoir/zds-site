from django.core.exceptions import PermissionDenied
from django.views.generic.base import ContextMixin, View

from zds.featured.managers import FeaturedRequestedException
from zds.featured.models import FeaturedRequested


class FeatureableMixin(ContextMixin, View):
    """Mixin for object that may be featured

    To be used with ``SingleObjectMixin`` or derived.
    """

    def toogle_featured_request(self, user=None):
        """Toogle featured request for user on ``self.object``

        :param user: the user
        :type user: User
        :rtype: (bool, int)
        """

        if not self.featured_request_allowed():
            raise PermissionDenied("request not allowed on this object")

        try:
            return FeaturedRequested.objects.toogle_request(self.object, user)
        except FeaturedRequestedException as e:
            raise PermissionDenied(e)

    def get_context_data(self, **kwargs):
        """Adds variables to template:

        - ``show_featured_requested``: show vote ?
        - ``is_requesting``: is current user requesting something?
        - ``featured_request_count``: number of votes ?
        """
        context = super().get_context_data(**kwargs)
        (
            context["show_featured_requested"],
            context["is_requesting"],
            context["featured_request_count"],
        ) = FeaturedRequested.objects.requested_and_count(self.object, self.request.user)

        context["show_featured_requested"] &= self.featured_request_allowed()

        return context

    def featured_request_allowed(self):
        """override this function if you want to add extra condition for a request to be allowed (or not)

        :rtype: bool
        """

        return True
