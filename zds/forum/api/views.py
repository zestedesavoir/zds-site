# coding: utf-8

from zds.member.api.permissions import CanReadTopic, CanReadPost, CanReadForum, CanReadAndWriteNowOrReadOnly, IsNotOwnerOrReadOnly, IsOwnerOrReadOnly, IsStaffUser
from zds.utils.api.views import KarmaView
from zds.forum.models import Post, Forum, Topic, Category
import datetime
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.http import Http404
from rest_framework import filters
from rest_framework.generics import ListAPIView, ListCreateAPIView, RetrieveUpdateAPIView, RetrieveAPIView, CreateAPIView
from rest_framework_extensions.key_constructor.constructors import DefaultKeyConstructor
from rest_framework_extensions.cache.decorators import cache_response
from rest_framework_extensions.etag.decorators import etag
from rest_framework_extensions.key_constructor import bits
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny, IsAuthenticated
from dry_rest_permissions.generics import DRYPermissions
from zds.api.bits import DJRF3xPaginationKeyBit, UpdatedAtKeyBit
from zds.utils import slugify
from zds.forum.api.serializer import ForumSerializer, TopicSerializer, TopicCreateSerializer, TopicUpdateSerializer, TopicUpdateStaffSerializer, PostSerializer, PostCreateSerializer, PostUpdateSerializer, AlertSerializer
from zds.forum.api.permissions import IsStaffUser, IsOwnerOrIsStaff, CanWriteInForum, CanWriteInTopic
from zds.member.models import User
from itertools import chain

class PostKarmaView(KarmaView):
    queryset = Post.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly, CanReadAndWriteNowOrReadOnly, IsNotOwnerOrReadOnly, CanReadPost)


class PagingSearchListKeyConstructor(DefaultKeyConstructor):
    pagination = DJRF3xPaginationKeyBit()
    list_sql_query = bits.ListSqlQueryKeyBit()
    unique_view_id = bits.UniqueViewIdKeyBit()
    user = bits.UserKeyBit()
    updated_at = UpdatedAtKeyBit('api_updated_forum')


class DetailKeyConstructor(DefaultKeyConstructor):
    format = bits.FormatKeyBit()
    language = bits.LanguageKeyBit()
    retrieve_sql_query = bits.RetrieveSqlQueryKeyBit()
    unique_view_id = bits.UniqueViewIdKeyBit()
    user = bits.UserKeyBit()
    updated_at = UpdatedAtKeyBit('api_updated_forum')


def change_api_forum_updated_at(sender=None, instance=None, *args, **kwargs):
    cache.set('forum_updated_tag', datetime.datetime.utcnow())


post_save.connect(receiver=change_api_forum_updated_at, sender=Forum)
post_delete.connect(receiver=change_api_forum_updated_at, sender=Forum)


class ForumListAPI(ListCreateAPIView):
    """
    Profile resource to list all forum.
    """
    serializer_class = ForumSerializer
    list_key_func = PagingSearchListKeyConstructor()

    @etag(list_key_func)
    @cache_response(key_func=list_key_func)
    def get(self, request, *args, **kwargs):
        """
        Lists all forum in the system.
        ---

        parameters:
            - name: page
              description: Restricts output to the given page number.
              required: false
              paramType: query
            - name: page_size
              description: Sets the number of forum per page.
              required: false
              paramType: query
        responseMessages:
            - code: 404
              message: Not Found
        """
        return self.list(request, *args, **kwargs)

    def get_queryset(self):
        public_forums = Forum.objects.filter(group__isnull=True).order_by('position_in_category')
        private_forums =  Forum.objects.filter(group__in=self.request.user.groups.all()).order_by('position_in_category')
        return public_forums | private_forums

    def get_permissions(self):
        permission_classes = [CanReadForum] # TODO style plus joli ?
        return [permission() for permission in permission_classes]


class ForumDetailAPI(RetrieveAPIView):
    """
    Profile resource to display details of a forum.
    ---
    """

    queryset = Forum.objects.all()
    obj_key_func = DetailKeyConstructor()
    serializer_class = ForumSerializer

    @etag(obj_key_func)
    @cache_response(key_func=obj_key_func)
    def get(self, request, *args, **kwargs):
        """
        Gets a forum given by its identifier.
        ---
        responseMessages:
            - code: 404
              message: Not Found
        """
        forum = self.get_object()

        return self.retrieve(request, *args, **kwargs)

    def get_serializer_class(self):
        return ForumSerializer

    def get_permissions(self):
        permission_classes = [CanReadForum] # TODO style plus joli ?
        return [permission() for permission in permission_classes]


class TopicListAPI(ListCreateAPIView):
    """
    Profile resource to list all topics (GET) or to create a topic (POST)
    """
    queryset = Topic.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('forum', 'author', 'tags__title')
    list_key_func = PagingSearchListKeyConstructor()

    @etag(list_key_func)
    @cache_response(key_func=list_key_func)
    def get(self, request, *args, **kwargs):
        """
        Lists all topic in a forum.
        ---

        parameters:
            - name: page
              description: Restricts output to the given page number.
              required: false
              paramType: query
            - name: page_size
              description: Sets the number of forum per page.
              required: false
              paramType: query
            - name: forum
              description: Filters by forum id.
              required: false
            - name: author
              description: Filters by author id.
              required: false
            - name: tags__title
              description: Filters by tag name.
              required: false
        responseMessages:
            - code: 404
              message: Not Found
        """

        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Creates a new topic.
        ---

        parameters:
            - name: Authorization
              description: Bearer token to make an authenticated request.
              required: true
              paramType: header
            - name: title
              description: Title of the Topic.
              required: true
              paramType: form
            - name: subtitle
              description: Subtitle of the Topic.
              required: false
              paramType: form
            - name: forum
              description: Identifier of the forum in which the Topic should be posted.
              required: false
              paramType: form
            - name: text
              description: Content of the first post in markdown.
              required: true
              paramType: form
            - name: tags
              description: To add a tag, specify its tag identifier. Specify this parameter
                           several times to add several tags.
              required: false
              paramType: form
        responseMessages:
            - code: 400
              message: Bad Request
            - code: 401
              message: Not Authenticated
            - code: 403
              message: Forbidden
        """
        author = request.user.id
        serializer = self.get_serializer_class()(data=request.data, context={'request': self.request})
        serializer.is_valid(raise_exception=True)
        serializer.save(author_id=author)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return TopicSerializer
        elif self.request.method == 'POST':
            return TopicCreateSerializer

    def get_permissions(self):
        permission_classes = [CanReadForum]
        if self.request.method == 'POST':
            print('requete post')

            #forum = Forum.objects.get(id=self.request.data.get('forum'))
            #self.check_object_permissions(self.request, forum)
            #permission_classes.append(CanReadAndWriteNowOrReadOnly)
            permission_classes.append(CanWriteInForum)
            permission_classes.append(CanReadAndWriteNowOrReadOnly)
        return [permission() for permission in permission_classes]


class UserTopicListAPI(ListAPIView):
    """
    Profile resource to list all topics from current user
    """

    serializer_class = TopicSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('forum', 'tags__title')
    list_key_func = PagingSearchListKeyConstructor()

    @etag(list_key_func)
    @cache_response(key_func=list_key_func)
    def get(self, request, *args, **kwargs):
        """
        Lists all topic from current user.
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
              description: Sets the number of forum per page.
              required: false
              paramType: query
        responseMessages:
            - code: 401
              message: Not Authenticated
            - code: 404
              message: Not Found
        """
        return self.list(request, *args, **kwargs)

    def get_queryset(self):
        topics = Topic.objects.filter(author=self.request.user)
        return topics

    def get_permissions(self):
        permission_classes = [AllowAny, IsAuthenticated]
        return [permission() for permission in permission_classes]


class TopicDetailAPI(RetrieveUpdateAPIView):
    """
    Profile resource to display and update details of a given topic
    """
    queryset = Topic.objects.all()
    obj_key_func = DetailKeyConstructor()

    @etag(obj_key_func)
    @cache_response(key_func=obj_key_func)
    def get(self, request, *args, **kwargs):
        """
        Gets a topic given by its identifier.
        ---
        responseMessages:
            - code: 401
              message: Not Authenticated
            - code: 403
              message: Forbidden
            - code: 404
              message: Not Found
        """
        topic = self.get_object()

        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        """
        Updates a topic. Said post must be owned by the authenticated member.
        ---

        parameters:
            - name: Authorization
              description: Bearer token to make an authenticated request.
              required: true
              paramType: header
            - name: title
              description: Title of the Topic.
              required: false
              paramType: form
            - name: subtitle
              description: Subtitle of the Topic.
              required: false
              paramType: form
            - name: text
              description: Content of the first post in markdown.
              required: false
              paramType: form
            - name: tags
              description: To add a tag, specify its taf identifier. Specify this parameter
                           several times to add several tags.
              required: false
              paramType: form
        responseMessages:
            - code: 400
              message: Bad Request if you specify a bad identifier
            - code: 401
              message: Not Authenticated
            - code: 403
              message: Permission Denied
            - code: 404
              message: Not Found
        """
        return self.update(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return TopicSerializer
        elif self.request.method == 'PUT':
            if self.request.user.has_perm("forum.change_topic"):
                return TopicUpdateStaffSerializer
            else:
                return TopicUpdateSerializer

    def get_permissions(self):
        permission_classes = []
        if self.request.method == 'GET':
            permission_classes.append(CanReadTopic)
        elif self.request.method == 'PUT':
            print(self.request.user)
            permission_classes.append(IsOwnerOrIsStaff)
            permission_classes.append(CanReadTopic)
        return [permission() for permission in permission_classes]


class PostListAPI(ListCreateAPIView):
    """
    Profile resource to list all messages in a topic
    """
    list_key_func = PagingSearchListKeyConstructor()

    @etag(list_key_func)
    @cache_response(key_func=list_key_func)
    def get(self, request, *args, **kwargs):
        """
        Lists all posts in a topic
        ---

        parameters:
            - name: page
              description: Restricts output to the given page number.
              required: false
              paramType: query
            - name: page_size
              description: Sets the number of forum per page.
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
        return self.list(request, *args, **kwargs)
        # TODO si message cache ? Le cacher dans l'API

    def post(self, request, *args, **kwargs):
        """
        Creates a new post in a topic.
        ---
        parameters:
            - name: Authorization
              description: Bearer token to make an authenticated request.
              required: true
              paramType: header
            - name: text
              description: Content of the post in markdown.
              required: true
              paramType: form
            - name: text
              description: Content of the first post in markdown.
              required: true
        responseMessages:
            - code: 400
              message: Bad Request
            - code: 401
              message: Not Authenticated
            - code: 403
              message: Permission Denied
            - code: 404
              message: Not Found
        """
        author = request.user.id
        topic = self.kwargs.get('pk')

        serializer = self.get_serializer_class()(data=request.data, context={'request': self.request})
        serializer.is_valid(raise_exception=True)
        serializer.save(position=0, author_id=author, topic_id=topic)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return PostSerializer
        elif self.request.method == 'POST':
            return PostCreateSerializer

    def get_queryset(self):
        if self.request.method == 'GET':
            posts = Post.objects.filter(topic=self.kwargs.get('pk'))
            if posts.count() == 0:
                raise Http404("Topic with pk {} was not found".format(self.kwargs.get('pk')))
        return posts

    def get_current_user(self):
        return self.request.user.profile

    def get_permissions(self):
        permission_classes = [CanReadPost]
        if self.request.method == 'POST':
            permission_classes.append(CanReadAndWriteNowOrReadOnly)
            permission_classes.append(CanWriteInTopic)

        return [permission() for permission in permission_classes]


class MemberPostListAPI(ListAPIView):
    """
    Profile resource to list all posts from a member
    """
    list_key_func = PagingSearchListKeyConstructor()
    serializer_class = PostSerializer

    @etag(list_key_func)
    @cache_response(key_func=list_key_func)
    def get(self, request, *args, **kwargs):
        """
        Lists all posts from a member
        ---

        parameters:
            - name: page
              description: Restricts output to the given page number.
              required: false
              paramType: query
            - name: page_size
              description: Sets the number of forum per page.
              required: false
              paramType: query
        responseMessages:
            - code: 404
              message: Not Found
        """
        return self.list(request, *args, **kwargs)
        # TODO fonctionne mais error xml sur certains post http://zds-anto59290.c9users.io/api/forums/membres/3/sujets

    def get_queryset(self):
        if self.request.method == 'GET':
            try:
                author = User.objects.get(pk = self.kwargs.get('pk'))
            except User.DoesNotExist:
                raise Http404("User with pk {} was not found".format(self.kwargs.get('pk')))

            # Gets every post of author visible by current user
            posts = Post.objects.get_all_messages_of_a_user(self.request.user, author)
        return posts


class UserPostListAPI(ListAPIView):
    """
    Profile resource to list all message from current user
    """

    list_key_func = PagingSearchListKeyConstructor()
    serializer_class = PostSerializer

    @etag(list_key_func)
    @cache_response(key_func=list_key_func)
    def get(self, request, *args, **kwargs):
        """
        Lists all posts from a current user.
        ---
        parameters:
            - name: page
              description: Restricts output to the given page number.
              required: false
              paramType: query
            - name: page_size
              description: Sets the number of forum per page.
              required: false
              paramType: query
        responseMessages:
            - code: 404
              message: Not Found
        """
        return self.list(request, *args, **kwargs)

    def get_queryset(self):
        if self.request.method == 'GET':
            posts = Post.objects.filter(author=self.request.user)
        return posts


class PostDetailAPI(RetrieveUpdateAPIView):
    """
    Profile resource to display details of given post
    """

    queryset = Post.objects.all()
    obj_key_func = DetailKeyConstructor()

    @etag(obj_key_func)
    @cache_response(key_func=obj_key_func)
    def get(self, request, *args, **kwargs):
        """
        Gets a post given by its identifier.
        ---
        responseMessages:
            - code: 401
              message: Not Authenticated
            - code: 403
              message: Permission Denied
            - code: 404
              message: Not Found
        """
        post = self.get_object()

        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        """
        Updates a post. Said post must be owned by the authenticated member.
        ---

        parameters:
            - name: Authorization
              description: Bearer token to make an authenticated request.
              required: true
              paramType: header
            - name: text
              description: Content of the post in markdown.
              required: true
              paramType: form
        responseMessages:
            - code: 400
              message: Bad Request if you specify a bad identifier
            - code: 401
              message: Not Authenticated
            - code: 403
              message: Permission Denied
            - code: 404
              message: Not Found
        """
        return self.update(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return PostSerializer
        elif self.request.method == 'PUT':
            return PostUpdateSerializer

    def get_permissions(self):
        permission_classes = [AllowAny, CanReadPost]
        if self.request.method == 'PUT':
            permission_classes.append(IsOwnerOrIsStaff)
            permission_classes.append(CanReadAndWriteNowOrReadOnly)
        return [permission() for permission in permission_classes]


class PostAlertAPI(CreateAPIView):
    """
    Alert a topic post to the staff.
    """

    def post(self, request, *args, **kwargs):
        """
        Alert a topic post to the staff.
        ---

        parameters:
            - name: Authorization
              description: Bearer token to make an authenticated request.
              required: true
              paramType: header
            - name: text
              description: Content of the alert in markdown.
              required: true
              paramType: form
        responseMessages:
            - code: 400
              message: Bad Request
            - code: 401
              message: Not Authenticated
            - code: 403
              message: Permission Denied
            - code: 404
              message: Not Found
        """
        author = request.user
        try:
            post = Post.objects.get(id=self.kwargs.get('pk'))
        except Post.DoesNotExist:
            raise Http404("Post with pk {} was not found".format(self.kwargs.get('pk')))

        serializer = self.get_serializer_class()(data=request.data, context={'request': self.request})
        serializer.is_valid(raise_exception=True)
        serializer.save(comment=post, pubdate=datetime.datetime.now(), author=author)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_permissions(self):
        permission_classes = [CanReadPost, IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        return AlertSerializer
