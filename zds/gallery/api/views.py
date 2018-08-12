from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import IsAuthenticated

from zds.gallery.models import UserGallery

from .serializers import GallerySerializer


class GalleryListView(ListCreateAPIView):

    def get(self, request, *args, **kwargs):
        """
        Lists an authenticated member's galleries
        ---

        parameters:
            - name: Authorization
              description: Bearer token to make an authenticated request.
              required: true
              paramType: header
            - name: page
              description: Restricts output to the given page number.
              required: false
              paramType: query
            - name: page_size
              description: Sets the number of private topics per page.
              required: false
              paramType: query
        responseMessages:
            - code: 401
              message: Not Authenticated
            - code: 404
              message: Not Found
        """
        return self.list(request, *args, **kwargs)

    def get_current_user(self):
        return self.request.user

    def get_serializer_class(self):
        return GallerySerializer

    def get_permissions(self):
        permission_classes = [IsAuthenticated, ]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        return UserGallery.objects.galleries_of_user(self.get_current_user())

    def post(self, request, *args, **kwargs):
        raise NotImplementedError()
