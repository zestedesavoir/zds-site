import datetime
import logging

from django.core.cache import cache
from django.db.models import Case, IntegerField, Value, When
from django.db.models.signals import post_delete, post_save
from django.utils.translation import gettext_lazy as _
from dry_rest_permissions.generics import DRYPermissions
from rest_framework import filters, status
from rest_framework.generics import (
    ListAPIView,
    ListCreateAPIView,
    RetrieveAPIView,
    RetrieveUpdateAPIView,
    get_object_or_404,
)
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework_extensions.cache.decorators import cache_response
from rest_framework_extensions.etag.decorators import etag
from rest_framework_extensions.key_constructor import bits
from rest_framework_extensions.key_constructor.constructors import DefaultKeyConstructor

from zds.api.bits import DJRF3xPaginationKeyBit, UpdatedAtKeyBit
from zds.member.api.generics import CreateDestroyMemberSanctionAPIView
from zds.member.api.permissions import IsOwnerOrReadOnly
from zds.member.api.serializers import (
    ProfileCreateSerializer,
    ProfileDetailSerializer,
    ProfileListSerializer,
    ProfileValidatorSerializer,
)
from zds.member.commons import (
    BanSanction,
    DeleteBanSanction,
    DeleteReadingOnlySanction,
    ProfileCreate,
    ReadingOnlySanction,
    TemporaryBanSanction,
    TemporaryReadingOnlySanction,
    TokenGenerator,
)
from zds.member.models import Profile


class PagingSearchListKeyConstructor(DefaultKeyConstructor):
    pagination = DJRF3xPaginationKeyBit()
    search = bits.QueryParamsKeyBit(["search"])
    list_sql_query = bits.ListSqlQueryKeyBit()
    unique_view_id = bits.UniqueViewIdKeyBit()
    user = bits.UserKeyBit()
    updated_at = UpdatedAtKeyBit("api_updated_profile")


class DetailKeyConstructor(DefaultKeyConstructor):
    format = bits.FormatKeyBit()
    language = bits.LanguageKeyBit()
    retrieve_sql_query = bits.RetrieveSqlQueryKeyBit()
    unique_view_id = bits.UniqueViewIdKeyBit()
    user = bits.UserKeyBit()
    updated_at = UpdatedAtKeyBit("api_updated_profile")


class MyDetailKeyConstructor(DefaultKeyConstructor):
    format = bits.FormatKeyBit()
    language = bits.LanguageKeyBit()
    user = bits.UserKeyBit()
    updated_at = UpdatedAtKeyBit("api_updated_profile")


def change_api_profile_updated_at(sender=None, instance=None, *args, **kwargs):
    cache.set("api_updated_profile", datetime.datetime.utcnow())


post_save.connect(receiver=change_api_profile_updated_at, sender=Profile)
post_delete.connect(receiver=change_api_profile_updated_at, sender=Profile)


class MemberListAPI(ListCreateAPIView, ProfileCreate, TokenGenerator):
    """
    Profile resource to list and register.
    """

    list_key_func = PagingSearchListKeyConstructor()

    def get_queryset(self):
        queryset = Profile.objects.contactable_members()
        search_param = self.request.query_params.get("search", None)

        if search_param:
            queryset = (
                queryset.filter(user__username__icontains=search_param)
                .annotate(
                    priority=Case(
                        When(user__username=search_param, then=Value(1)),
                        When(user__username__iexact=search_param, then=Value(2)),
                        When(user__username__startswith=search_param, then=Value(3)),
                        When(user__username__istartswith=search_param, then=Value(4)),
                        When(user__username__contains=search_param, then=Value(5)),
                        default=Value(6),
                        output_field=IntegerField(),
                    )
                )
                .order_by("priority", "user__username")
            )

        return queryset

    @etag(list_key_func)
    @cache_response(key_func=list_key_func)
    def get(self, request, *args, **kwargs):
        """
        Lists all users in the system.
        ---

        parameters:
            - name: page
              description: Restricts output to the given page number.
              required: false
              paramType: query
            - name: page_size
              description: Sets the number of profiles per page.
              required: false
              paramType: query
            - name: search
              description: Filters by username.
              required: false
              paramType: query
        responseMessages:
            - code: 404
              message: Not Found
        """
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Registers a new user. User will need to act on confirmation email.
        ---

        responseMessages:
            - code: 400
              message: Bad Request
        """
        serializer = self.get_serializer_class()(data=request.data, context={"request": self.request})
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()
        token = self.generate_token(profile.user)
        try:
            self.send_email(token, profile.user)
        except Exception as e:
            logging.getLogger(__name__).warning("Mail not sent", exc_info=e)
            return Response({"error": _("Impossible d'envoyer l'email")}, status=status.HTTP_400_BAD_REQUEST)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ProfileListSerializer
        elif self.request.method == "POST":
            return ProfileCreateSerializer

    def get_permissions(self):
        permission_classes = [
            AllowAny,
        ]
        if self.request.method == "GET" or self.request.method == "POST":
            permission_classes.append(DRYPermissions)
        return [permission() for permission in permission_classes]


class MemberExistsAPI(ListAPIView):
    """
    Profile resource to get if a username exists.
    """

    filter_backends = (filters.SearchFilter,)
    search_fields = ("=user__username",)
    list_key_func = PagingSearchListKeyConstructor()
    serializer_class = ProfileDetailSerializer

    def get_queryset(self):
        return Profile.objects.contactable_members()

    @etag(list_key_func)
    @cache_response(key_func=list_key_func)
    def get(self, request, *args, **kwargs):
        """
        Get if a username exists.
        ---

        parameters:
            - name: page
              description: Restricts output to the given page number.
              required: false
              paramType: query
            - name: page_size
              description: Sets the number of profiles per page.
              required: false
              paramType: query
            - name: search
              description: Filters by username.
              required: false
              paramType: query
        responseMessages:
            - code: 404
              user doesn't exists.
        """
        r = self.list(request, *args, **kwargs)
        if r.data["count"] == 0:
            return Response(r.data, status=status.HTTP_404_NOT_FOUND)
        return r

    def get_permissions(self):
        permission_classes = [
            AllowAny,
        ]
        if self.request.method == "GET":
            permission_classes.append(DRYPermissions)
        return [permission() for permission in permission_classes]


class MemberMyDetailAPI(RetrieveAPIView):
    """
    Profile resource for member details.
    """

    obj_key_func = MyDetailKeyConstructor()
    serializer_class = ProfileDetailSerializer

    @etag(obj_key_func)
    @cache_response(key_func=obj_key_func)
    def get(self, request, *args, **kwargs):
        """
        Gets information for a user account.
        ---

        parameters:
            - name: Authorization
              description: Bearer token to make an authenticated request.
              required: true
              paramType: header
        responseMessages:
            - code: 401
              message: Not Authenticated
        """
        profile = self.get_object()
        serializer = self.get_serializer(profile, show_email=True, is_authenticated=True)
        return Response(serializer.data)

    def get_object(self):
        return get_object_or_404(Profile, user=self.request.user)

    def get_permissions(self):
        permission_classes = [
            IsAuthenticated,
        ]
        if self.request.method == "GET":
            permission_classes.append(DRYPermissions)
        return [permission() for permission in permission_classes]


class MemberDetailAPI(RetrieveUpdateAPIView):
    """
    Profile resource to display or update details of a member.
    """

    queryset = Profile.objects.all()
    lookup_field = "user__id"
    obj_key_func = DetailKeyConstructor()

    @etag(obj_key_func)
    @cache_response(key_func=obj_key_func)
    def get(self, request, *args, **kwargs):
        """
        Gets a user given by its identifier.
        ---

        parameters:
            - name: Authorization
              description: Bearer token to make an authenticated request.
              required: false
              paramType: header
        responseMessages:
            - code: 404
              message: Not Found
        """
        profile = self.get_object()
        serializer = self.get_serializer(
            profile, show_email=profile.show_email, is_authenticated=self.request.user.is_authenticated
        )
        return Response(serializer.data)

    @etag(obj_key_func, rebuild_after_method_evaluation=True)
    def put(self, request, *args, **kwargs):
        """
        Updates a user given by its identifier.
        ---

        parameters:
            - name: Authorization
              description: Bearer token to make an authenticated request.
              required: true
              paramType: header
        responseMessages:
            - code: 400
              message: Bad Request
            - code: 401
              message: Not Authenticated
            - code: 403
              message: Insufficient rights to call this procedure. Source and target users must be equal.
            - code: 404
              message: Not Found
        """
        return self.update(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ProfileDetailSerializer
        elif self.request.method == "PUT":
            return ProfileValidatorSerializer
        else:  # used only for API documentation
            return ProfileDetailSerializer

    def get_permissions(self):
        permission_classes = []
        if self.request.method == "GET":
            permission_classes.append(DRYPermissions)
        elif self.request.method == "PUT":
            permission_classes.append(DRYPermissions)
            permission_classes.append(IsAuthenticatedOrReadOnly)
            permission_classes.append(IsOwnerOrReadOnly)
        return [permission() for permission in permission_classes]


class MemberDetailReadingOnly(CreateDestroyMemberSanctionAPIView):
    """
    Profile resource to apply or remove read only sanction.
    """

    lookup_field = "user__id"

    def post(self, request, *args, **kwargs):
        """
        Applies a read only sanction to the given user.
        ---

        parameters:
            - name: Authorization
              description: Bearer token to make an authenticated request.
              required: true
              paramType: header
            - name: ls-jrs
              description: Sanction duration in days.
              required: false
              paramType: form
            - name: ls-text
              description: Description of the sanction.
              required: false
              paramType: form
        omit_parameters:
            - body
        responseMessages:
            - code: 401
              message: Not Authenticated
            - code: 403
              message: Insufficient rights to call this procedure. Needs staff status.
            - code: 404
              message: Not Found
        """
        return super().post(request, args, kwargs)

    def delete(self, request, *args, **kwargs):
        """
        Removes a read only sanction from the given user.
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
              message: Insufficient rights to call this procedure. Needs staff status.
            - code: 404
              message: Not Found
        """
        return super().delete(request, args, kwargs)

    def get_state_instance(self, request):
        if request.method == "POST":
            if "ls-jrs" in request.data:
                return TemporaryReadingOnlySanction(request.data)
            else:
                return ReadingOnlySanction(request.data)
        elif request.method == "DELETE":
            return DeleteReadingOnlySanction(request.data)
        raise ValueError(f"Method {request.method} is not supported in this API route.")


class MemberDetailBan(CreateDestroyMemberSanctionAPIView):
    """
    Profile resource to apply or remove ban sanction.
    """

    lookup_field = "user__id"

    def post(self, request, *args, **kwargs):
        """
        Applies a ban sanction to a given user.
        ---

        parameters:
            - name: Authorization
              description: Bearer token to make an authenticated request.
              required: true
              paramType: header
            - name: ban-jrs
              description: Sanction duration in days.
              required: false
              paramType: form
            - name: ban-text
              description: Description of the sanction.
              required: false
              paramType: form
        omit_parameters:
            - body
        responseMessages:
            - code: 401
              message: Not Authenticated
            - code: 403
              message: Insufficient rights to call this procedure. Needs staff status.
            - code: 404
              message: Not Found
        """
        return super().post(request, args, kwargs)

    def delete(self, request, *args, **kwargs):
        """
        Removes a ban sanction from a given user.
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
              message: Insufficient rights to call this procedure. Needs staff status.
            - code: 404
              message: Not Found
        """
        return super().delete(request, args, kwargs)

    def get_state_instance(self, request):
        if request.method == "POST":
            if "ban-jrs" in request.data:
                return TemporaryBanSanction(request.data)
            else:
                return BanSanction(request.POST)
        elif request.method == "DELETE":
            return DeleteBanSanction(request.data)
        raise ValueError(f"Method {request.method} is not supported in this API route.")
