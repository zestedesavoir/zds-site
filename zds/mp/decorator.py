from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404

from zds.mp.models import PrivatePost, PrivateTopic


def is_participant(func):
    """
    Checks if the current user is a participant of the private topic specified in the URL
    and if the post specified in the GET parameter `cite` is on the private topic.
    :param func: the decorated function
    :return: `True` if the current user can read and write, `False` otherwise.
    """

    def _is_participant(request, *args, **kwargs):
        private_topic = get_object_or_404(PrivateTopic, pk=kwargs.get("pk"))
        if not private_topic.is_participant(request.user):
            raise PermissionDenied
        if "cite" in request.GET:
            try:
                if (
                    PrivatePost.objects.filter(privatetopic=private_topic)
                    .filter(pk=int(request.GET.get("cite")))
                    .count()
                    != 1
                ):
                    raise PermissionDenied
            except ValueError:
                raise Http404
        return func(request, *args, **kwargs)

    return _is_participant
