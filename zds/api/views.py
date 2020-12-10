from rest_framework import exceptions


class NoPatchView:
    """Raise HTTP 405 if one try to use the patch method"""

    def patch(self, request, *args, **kwargs):
        raise exceptions.MethodNotAllowed(method="PATCH")
