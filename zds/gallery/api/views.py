from django.utils.translation import gettext_lazy as _
from dry_rest_permissions.generics import DRYPermissions
from rest_framework import exceptions, filters
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_extensions.cache.decorators import cache_response
from rest_framework_extensions.etag.decorators import etag
from rest_framework_extensions.key_constructor import bits

from zds.api.bits import UpdatedAtKeyBit
from zds.api.key_constructor import DetailKeyConstructor, PagingListKeyConstructor
from zds.api.views import NoPatchView
from zds.gallery.mixins import GalleryUpdateOrDeleteMixin, ImageUpdateOrDeleteMixin, NoMoreUserWithWriteIfLeave
from zds.gallery.models import Gallery, Image, UserGallery

from .permissions import AccessToGallery, NotLinkedToContent, WriteAccessToGallery
from .serializers import GallerySerializer, ImageSerializer, ParticipantSerializer


class PagingGalleryListKeyConstructor(PagingListKeyConstructor):
    search = bits.QueryParamsKeyBit(["search", "ordering"])
    user = bits.UserKeyBit()
    updated_at = UpdatedAtKeyBit("api_updated_gallery")


class GalleryListView(ListCreateAPIView):
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ("title",)
    ordering_fields = ("title", "update", "pubdate")
    list_key_func = PagingGalleryListKeyConstructor()

    @etag(list_key_func)
    @cache_response(key_func=list_key_func)
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
              description: Sets the number of galleries per page.
              required: false
              paramType: query
            - name: search
              description: Filters by title.
              required: false
              paramType: query
            - name: ordering
              description: Sorts the results. You can order by (-)title, (-)update, (-)pubdate.
              paramType: query
        responseMessages:
            - code: 401
              message: Not Authenticated
        """
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Create a new gallery
        ---

        parameters:
            - name: Authorization
              description: Bearer token to make an authenticated request.
              required: true
              paramType: header
            - name: title
              description: Gallery title.
              required: true
              paramType: form
            - name: subtitle
              description: Gallery subtitle.
              required: false
              paramType: form
        """
        return self.create(request, *args, **kwargs)

    def get_current_user(self):
        return self.request.user

    def get_serializer_class(self):
        return GallerySerializer

    def get_permissions(self):
        permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        return Gallery.objects.galleries_of_user(self.get_current_user()).order_by("pk")


class GalleryDetailKeyConstructor(DetailKeyConstructor):
    user = bits.UserKeyBit()
    updated_at = UpdatedAtKeyBit("api_updated_gallery")


class GalleryDetailView(RetrieveUpdateDestroyAPIView, NoPatchView, GalleryUpdateOrDeleteMixin):
    queryset = Gallery.objects.annotated_gallery()
    list_key_func = GalleryDetailKeyConstructor()

    @etag(list_key_func)
    @cache_response(key_func=list_key_func)
    def get(self, request, *args, **kwargs):
        """
        Gets a gallery by identifier.
        ---

        parameters:
            - name: Authorization
              description: Bearer token to make an authenticated request.
              required: true
              paramType: header
            - name: expand
              description: Returns an object instead of an identifier representing the given field.
              required: false
              paramType: query
        responseMessages:
            - code: 401
              message: Not Authenticated
            - code: 403
              message: Permission Denied
            - code: 404
              message: Not Found
        """

        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        """
        Update the gallery
        ---

        parameters:
            - name: Authorization
              description: Bearer token to make an authenticated request.
              required: true
              paramType: header
            - name: title
              description: Gallery title.
              required: true
              paramType: form
            - name: subtitle
              description: Gallery subtitle.
              required: false
              paramType: form
        responseMessages:
            - code: 401
              message: Not Authenticated
            - code: 403
              message: Permission Denied
            - code: 404
              message: Not Found
        """
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        """
        Deletes a gallery
        ---

        parameters:
            - name: Authorization
              description: Bearer token to make an authenticated request.
              required: true
              paramType: header
        responseMessages:
            - code: 401
              message: Not Authenticated
            - code: 403
              message: Permission Denied
            - code: 404
              message: Not Found
        """
        return self.destroy(request, *args, **kwargs)

    def perform_destroy(self, instance):
        self.gallery = instance
        self.perform_delete()

    def get_current_user(self):
        return self.request.user

    def get_serializer_class(self):
        return GallerySerializer

    def get_permissions(self):
        permission_classes = [IsAuthenticated, DRYPermissions]
        if self.request.method in ["PUT", "DELETE"]:
            permission_classes.append(NotLinkedToContent)
        return [permission() for permission in permission_classes]


class PagingImageListKeyConstructor(PagingListKeyConstructor):
    search = bits.QueryParamsKeyBit(["search", "ordering"])
    user = bits.UserKeyBit()
    updated_at = UpdatedAtKeyBit("api_updated_image")


class ImageListView(ListCreateAPIView):
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ("title",)
    ordering_fields = ("title", "update", "pubdate")
    list_key_func = PagingImageListKeyConstructor()

    @etag(list_key_func)
    @cache_response(key_func=list_key_func)
    def get(self, request, *args, **kwargs):
        """
        Lists images from a given gallery
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
              description: Sets the number of galleries per page.
              required: false
              paramType: query
            - name: search
              description: Filters by title.
              required: false
              paramType: query
            - name: ordering
              description: Sorts the results. You can order by (-)title, (-)update, (-)pubdate.
              paramType: query
        responseMessages:
            - code: 401
              message: Not Authenticated
            - code: 403
              message: Permission Denied
            - code: 404
              message: Not Found
        """
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Upload a new image
        ---

        parameters:
            - name: Authorization
              description: Bearer token to make an authenticated request.
              required: true
              paramType: header
            - name: title
              description: Image title
              required: true
              paramType: form
            - name: legend
              description: Image small legend (one line)
              required: false
              paramType: form
            - name: physical
              description: Image data
              required: true
              consumes: multipart/form-data
              paramType: form
        responseMessages:
            - code: 401
              message: Not Authenticated
            - code: 403
              message: Permission Denied
            - code: 404
              message: Not Found
        """

        return self.create(request, *args, **kwargs)

    def get_current_user(self):
        return self.request.user

    def get_serializer_class(self):
        return ImageSerializer

    def get_permissions(self):
        permission_classes = [IsAuthenticated, AccessToGallery]
        if self.request.method == "POST":
            permission_classes.append(WriteAccessToGallery)
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        return Image.objects.filter(gallery__pk=self.kwargs.get("pk_gallery"))


class ImageDetailKeyConstructor(DetailKeyConstructor):
    user = bits.UserKeyBit()
    updated_at = UpdatedAtKeyBit("api_updated_image")


class ImageDetailView(RetrieveUpdateDestroyAPIView, NoPatchView, ImageUpdateOrDeleteMixin):
    queryset = Image.objects
    list_key_func = ImageDetailKeyConstructor()

    @etag(list_key_func)
    @cache_response(key_func=list_key_func)
    def get(self, request, *args, **kwargs):
        """
        Gets an image by identifier.
        ---

        parameters:
            - name: Authorization
              description: Bearer token to make an authenticated request.
              required: true
              paramType: header
            - name: expand
              description: Returns an object instead of an identifier representing the given field.
              required: false
              paramType: query
        responseMessages:
            - code: 401
              message: Not Authenticated
            - code: 403
              message: Permission Denied
            - code: 404
              message: Not Found
        """

        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        """
        Update an image
        ---

        parameters:
            - name: Authorization
              description: Bearer token to make an authenticated request.
              required: true
              paramType: header
            - name: title
              description: Image title.
              required: true
              paramType: form
            - name: legend
              description: Image small legend (one line)
              required: false
              paramType: form
            - name: physical
              description: Image data
              required: true
              consumes: multipart/form-data
              paramType: form
        responseMessages:
            - code: 401
              message: Not Authenticated
            - code: 403
              message: Permission Denied
            - code: 404
              message: Not Found
        """
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        """
        Delete an image
        ---

        parameters:
            - name: Authorization
              description: Bearer token to make an authenticated request.
              required: true
              paramType: header
        responseMessages:
            - code: 401
              message: Not Authenticated
            - code: 403
              message: Permission Denied
            - code: 404
              message: Not Found
        """
        return self.destroy(request, *args, **kwargs)

    def get_current_user(self):
        return self.request.user

    def perform_destroy(self, instance):
        self.image = instance
        self.perform_delete()

    def get_serializer_class(self):
        return ImageSerializer

    def get_permissions(self):
        permission_classes = [IsAuthenticated, DRYPermissions]
        return [permission() for permission in permission_classes]


class PagingParticipantListKeyConstructor(PagingListKeyConstructor):
    search = bits.QueryParamsKeyBit(["ordering"])
    user = bits.UserKeyBit()
    updated_at = UpdatedAtKeyBit("api_updated_user_gallery")


class ParticipantListView(ListCreateAPIView):
    filter_backends = (filters.OrderingFilter,)
    ordering_fields = ("id",)
    list_key_func = PagingParticipantListKeyConstructor()

    @etag(list_key_func)
    @cache_response(key_func=list_key_func)
    def get(self, request, *args, **kwargs):
        """
        Lists participants of a given gallery
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
              description: Sets the number of galleries per page.
              required: false
              paramType: query
            - name: ordering
              description: Sorts the results. You can order by (-)title, (-)update, (-)pubdate.
              paramType: query
        responseMessages:
            - code: 401
              message: Not Authenticated
            - code: 403
              message: Permission Denied
            - code: 404
              message: Not Found
        """
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Add participant
        ---

        parameters:
            - name: Authorization
              description: Bearer token to make an authenticated request.
              required: true
              paramType: header
            - name: id
              description: Valid user id
              required: true
              paramType: form
            - name: can_write
              description: does the user have write access to the gallery ?
              required: true
              paramType: form
        """
        return self.create(request, *args, **kwargs)

    def get_current_user(self):
        return self.request.user

    def get_serializer_class(self):
        return ParticipantSerializer

    def get_permissions(self):
        permission_classes = [IsAuthenticated, AccessToGallery]
        if self.request.method == "POST":
            permission_classes.append(WriteAccessToGallery)
            permission_classes.append(NotLinkedToContent)

        return [permission() for permission in permission_classes]

    def get_queryset(self):
        return UserGallery.objects.filter(gallery__pk=self.kwargs.get("pk_gallery"))


class ParticipantDetailKeyConstructor(DetailKeyConstructor):
    user = bits.UserKeyBit()
    updated_at = UpdatedAtKeyBit("api_updated_user_gallery")


class ParticipantDetailView(RetrieveUpdateDestroyAPIView, NoPatchView, GalleryUpdateOrDeleteMixin):
    list_key_func = ParticipantDetailKeyConstructor()
    lookup_field = "user__pk"

    @etag(list_key_func)
    @cache_response(key_func=list_key_func)
    def get(self, request, *args, **kwargs):
        """
        Get a participant by its id
        ---

        parameters:
            - name: Authorization
              description: Bearer token to make an authenticated request.
              required: true
              paramType: header
        responseMessages:
            - code: 401
              message: Not Authenticated
            - code: 403
              message: Permission Denied
            - code: 404
              message: Not Found
        """

        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        """
        Update a participant
        ---

        parameters:
            - name: Authorization
              description: Bearer token to make an authenticated request.
              required: true
              paramType: header
            - name: can_write
              description: does the user have write access to the gallery ?
              required: true
              paramType: form
        responseMessages:
            - code: 401
              message: Not Authenticated
            - code: 403
              message: Permission Denied
            - code: 404
              message: Not Found
        """
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        """
        Remove participant
        ---

        parameters:
            - name: Authorization
              description: Bearer token to make an authenticated request.
              required: true
              paramType: header
        responseMessages:
            - code: 401
              message: Not Authenticated
            - code: 403
              message: Permission Denied
            - code: 404
              message: Not Found
        """
        return self.destroy(request, *args, **kwargs)

    def perform_destroy(self, instance):
        self.gallery = instance.gallery
        self.users_and_permissions = self.gallery.get_users_and_permissions()

        try:
            self.perform_leave(instance.user)
        except NoMoreUserWithWriteIfLeave:
            raise exceptions.PermissionDenied(
                detail=_(
                    "Vous ne pouvez pas quitter la galerie, "
                    "car plus aucun autre participant n'a les droits d'écriture"
                )
            )

    def get_current_user(self):
        return self.request.user

    def get_serializer_class(self):
        return ParticipantSerializer

    def get_permissions(self):
        permission_classes = [IsAuthenticated, AccessToGallery]
        if self.request.method in ["PUT", "DELETE"]:
            permission_classes.append(WriteAccessToGallery)
            permission_classes.append(NotLinkedToContent)

        return [permission() for permission in permission_classes]

    def get_queryset(self):
        return UserGallery.objects.filter(gallery__pk=self.kwargs.get("pk_gallery"))
