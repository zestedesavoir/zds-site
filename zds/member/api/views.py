# -*- coding: utf-8 -*-

from rest_framework import filters
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateAPIView, RetrieveAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_extensions.cache.decorators import cache_response
from rest_framework_extensions.etag.decorators import etag
from rest_framework_extensions.key_constructor import bits
from rest_framework_extensions.key_constructor.constructors import DefaultKeyConstructor
from zds.api.DJRF3xPaginationKeyBit import DJRF3xPaginationKeyBit

from zds.member.api.serializers import ProfileListSerializer, ProfileCreateSerializer, \
    ProfileDetailSerializer, ProfileValidatorSerializer
from zds.member.api.permissions import IsOwnerOrReadOnly
from zds.member.api.generics import CreateDestroyMemberSanctionAPIView
from zds.member.commons import TemporaryReadingOnlySanction, ReadingOnlySanction, \
    DeleteReadingOnlySanction, TemporaryBanSanction, BanSanction, DeleteBanSanction, \
    ProfileCreate, TokenGenerator
from zds.member.models import Profile


class PagingSearchListKeyConstructor(DefaultKeyConstructor):
    pagination = DJRF3xPaginationKeyBit()
    search = bits.QueryParamsKeyBit(['search'])
    list_sql_query = bits.ListSqlQueryKeyBit()
    unique_view_id = bits.UniqueViewIdKeyBit()


class DetailKeyConstructor(DefaultKeyConstructor):
    format = bits.FormatKeyBit()
    language = bits.LanguageKeyBit()
    retrieve_sql_query = bits.RetrieveSqlQueryKeyBit()
    unique_view_id = bits.UniqueViewIdKeyBit()


class MyDetailKeyConstructor(DefaultKeyConstructor):
    format = bits.FormatKeyBit()
    language = bits.LanguageKeyBit()


class MemberListAPI(ListCreateAPIView, ProfileCreate, TokenGenerator):
    """
    Profile resource to list and register.
    """

    queryset = Profile.objects.all_members_ordered_by_date_joined()
    filter_backends = (filters.SearchFilter,)
    search_fields = ('user__username',)
    list_key_func = PagingSearchListKeyConstructor()

    @etag(list_key_func)
    @cache_response(key_func=list_key_func)
    def get(self, request, *args, **kwargs):
        """
        Lists all users in the system.
        ---

        parameters:
            - name: page
              description: Displays users of the page given.
              required: false
              paramType: query
            - name: page_size
              description: Sets size of the pagination.
              required: false
              paramType: query
            - name: search
              description: Makes a search on the username.
              required: false
              paramType: query
        responseMessages:
            - code: 404
              message: Not found
        """
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Registers a new user in the system. The user must confirm its registration.
        ---

        responseMessages:
            - code: 400
              message: Bad Request
        """
        self.permission_classes = (AllowAny,)
        serializer = self.get_serializer_class()(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()
        token = self.generate_token(profile.user)
        self.send_email(token, profile.user)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ProfileListSerializer
        elif self.request.method == 'POST':
            return ProfileCreateSerializer


class MemberMyDetailAPI(RetrieveAPIView):
    """
    Profile resource to display details of the member.
    """
    obj_key_func = MyDetailKeyConstructor()
    permission_classes = (IsAuthenticated,)
    serializer_class = ProfileDetailSerializer

    @etag(obj_key_func)
    @cache_response(key_func=obj_key_func)
    def get(self, request, *args, **kwargs):
        """
        Gets information of his account.
        ---

        parameters:
            - name: Authorization
              description: Bearer token to make a authenticated request.
              required: true
              paramType: header
        responseMessages:
            - code: 401
              message: Not authenticated
        """
        profile = self.get_object()
        serializer = self.get_serializer(profile,
                                         show_email=True,
                                         is_authenticated=True)
        return Response(serializer.data)

    def get_object(self):
        return get_object_or_404(Profile, user=self.request.user)


class MemberDetailAPI(RetrieveUpdateAPIView):
    """
    Profile resource to display or update details of a member.
    """

    queryset = Profile.objects.all()
    lookup_field = 'user__id'
    obj_key_func = DetailKeyConstructor()

    @etag(obj_key_func)
    @cache_response(key_func=obj_key_func)
    def get(self, request, *args, **kwargs):
        """
        Gets a user given by its identifier.
        ---

        parameters:
            - name: Authorization
              description: Bearer token to make a authenticated request.
              required: false
              paramType: header
        responseMessages:
            - code: 404
              message: Not found
        """
        profile = self.get_object()
        serializer = self.get_serializer(profile,
                                         show_email=profile.show_email,
                                         is_authenticated=self.request.user.is_authenticated())
        return Response(serializer.data)

    @etag(obj_key_func, rebuild_after_method_evaluation=True)
    def put(self, request, *args, **kwargs):
        """
        Updates a user given by its identifier.
        ---

        parameters:
            - name: Authorization
              description: Bearer token to make a authenticated request.
              required: true
              paramType: header
        responseMessages:
            - code: 400
              message: Bad Request
            - code: 401
              message: Not authenticated
            - code: 403
              message: Insufficient rights to call this procedure. Source and target user must to be equals.
            - code: 404
              message: Not found
        """
        self.permission_classes = (IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly)
        return self.update(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ProfileDetailSerializer
        elif self.request.method == 'PUT':
            return ProfileValidatorSerializer


class MemberDetailReadingOnly(CreateDestroyMemberSanctionAPIView):
    """
    Profile resource to apply or remove read only sanction.
    """

    lookup_field = 'user__id'

    def post(self, request, *args, **kwargs):
        """
        Applies a read only sanction at a user given.
        ---

        parameters:
            - name: Authorization
              description: Bearer token to make a authenticated request.
              required: true
              paramType: header
            - name: ls-jrs
              description: Number of days for the sanction.
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
              message: Not authenticated
            - code: 403
              message: Insufficient rights to call this procedure. Must to be a staff user.
            - code: 404
              message: Not found
        """
        return super(MemberDetailReadingOnly, self).post(request, args, kwargs)

    def delete(self, request, *args, **kwargs):
        """
        Removes a read only sanction at a user given.
        ---

        parameters:
            - name: Authorization
              description: Bearer token to make a authenticated request.
              required: true
              paramType: header
        responseMessages:
            - code: 401
              message: Not authenticated
            - code: 403
              message: Insufficient rights to call this procedure. Must to be a staff user.
            - code: 404
              message: Not found
        """
        return super(MemberDetailReadingOnly, self).delete(request, args, kwargs)

    def get_state_instance(self, request):
        if request.method == 'POST':
            if 'ls-jrs' in request.POST:
                return TemporaryReadingOnlySanction(request.POST)
            else:
                return ReadingOnlySanction(request.POST)
        elif request.method == 'DELETE':
            return DeleteReadingOnlySanction(request.POST)
        raise ValueError('Method {0} is not supported in this route of the API.'.format(request.method))


class MemberDetailBan(CreateDestroyMemberSanctionAPIView):
    """
    Profile resource to apply or remove ban sanction.
    """

    lookup_field = 'user__id'

    def post(self, request, *args, **kwargs):
        """
        Applies a ban sanction at a user given.
        ---

        parameters:
            - name: Authorization
              description: Bearer token to make a authenticated request.
              required: true
              paramType: header
            - name: ban-jrs
              description: Number of days for the sanction.
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
              message: Not authenticated
            - code: 403
              message: Insufficient rights to call this procedure. Must to be a staff user.
            - code: 404
              message: Not found
        """
        return super(MemberDetailBan, self).post(request, args, kwargs)

    def delete(self, request, *args, **kwargs):
        """
        Removes a ban sanction at a user given.
        ---

        parameters:
            - name: Authorization
              description: Bearer token to make a authenticated request.
              required: true
              paramType: header
        responseMessages:
            - code: 401
              message: Not authenticated
            - code: 403
              message: Insufficient rights to call this procedure. Must to be a staff user.
            - code: 404
              message: Not found
        """
        return super(MemberDetailBan, self).delete(request, args, kwargs)

    def get_state_instance(self, request):
        if request.method == 'POST':
            if 'ban-jrs' in request.POST:
                return TemporaryBanSanction(request.POST)
            else:
                return BanSanction(request.POST)
        elif request.method == 'DELETE':
            return DeleteBanSanction(request.POST)
        raise ValueError('Method {0} is not supported in this route of the API.'.format(request.method))
