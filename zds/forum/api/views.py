# coding: utf-8

from zds.member.api.permissions import CanReadTopic, CanReadAndWriteNowOrReadOnly, IsNotOwnerOrReadOnly
from zds.utils.api.views import KarmaView
from zds.forum.models import Post, Forum, Topic
import datetime
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from rest_framework import filters
from rest_framework.generics import ListAPIView
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateAPIView
from rest_framework_extensions.key_constructor.constructors import DefaultKeyConstructor
from rest_framework_extensions.cache.decorators import cache_response
from rest_framework_extensions.etag.decorators import etag
from rest_framework_extensions.key_constructor import bits
from zds.api.bits import DJRF3xPaginationKeyBit, UpdatedAtKeyBit
from zds.utils import slugify
from zds.forum.api.serializer import ForumSerializer, TopicSerializer, TopicActionSerializer, PostSerializer, PostActionSerializer, ForumActionSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny, IsAuthenticated
from dry_rest_permissions.generics import DRYPermissions
from zds.forum.api.permissions import IsStaffUser
from django.http import HttpResponseRedirect

class PostKarmaView(KarmaView):
    queryset = Post.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly, CanReadAndWriteNowOrReadOnly, IsNotOwnerOrReadOnly, CanReadTopic)


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
    Profile resource to list all forum
    """

    queryset = Forum.objects.all()
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
        
    def post(self, request, *args, **kwargs):
        """
        Creates a new forum.
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
              message: Bad Request
            - code: 401
              message: Not Authenticated
            - code: 403
              message: Permission Denied
        """

        forum_slug = slugify(request.data.get('title'))
        serializer = self.get_serializer_class()(data=request.data, context={'request': self.request})
        serializer.is_valid(raise_exception=True)
        serializer.save(slug=forum_slug)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ForumSerializer
        elif self.request.method == 'POST':
            return ForumActionSerializer

    def get_permissions(self):
        permission_classes = [AllowAny, ]
        if self.request.method == 'POST':
            permission_classes.append(DRYPermissions)
            permission_classes.append(IsStaffUser)
        return [permission() for permission in permission_classes]


class ForumDetailAPI(RetrieveUpdateAPIView):
    """
    Profile resource to display or update details of a forum.
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
        serializer = self.get_serializer(forum)
        
        return self.retrieve(request, *args, **kwargs)
        

class TopicListAPI(ListCreateAPIView):
    """
    Profile resource to list all topic
    """
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('forum','author','tags__title')
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
            - name: text
              description: Content of the post in markdown.
              required: true
              paramType: form
        responseMessages:
            - code: 400
              message: Bad Request
            - code: 401
              message: Not Authenticated
        """

        author = request.user
        
        serializer = self.get_serializer_class()(data=request.data, context={'request': self.request})
        serializer.is_valid(raise_exception=True)
        topic = serializer.save(author_id=3)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return TopicSerializer
        elif self.request.method == 'POST':
            return TopicActionSerializer


    def get_permissions(self):
        permission_classes = [AllowAny, ]
        if self.request.method == 'POST':
            permission_classes.append(DRYPermissions)
            permission_classes.append(IsAuthenticated)
        return [permission() for permission in permission_classes]
    
        

class UserTopicListAPI(ListAPIView):
    """
    Profile resource to list all topic from current user
    """

    serializer_class = TopicSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('forum','tags__title')
    list_key_func = PagingSearchListKeyConstructor()


    @etag(list_key_func)
    @cache_response(key_func=list_key_func)
    def get(self, request, *args, **kwargs):
        """
        Lists all topic from current user.
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
        # TODO code d'auth manquant en commentaire
        return self.list(request, *args, **kwargs)
        
    def get_queryset(self):
        topics = Topic.objects.filter(author=self.request.user)
        return topics


class TopicDetailAPI(RetrieveUpdateAPIView):
    """
    Profile resource to display details of a given topic
    """
    
    queryset = Topic.objects.all()
    obj_key_func = DetailKeyConstructor()
    serializer_class = TopicSerializer

    @etag(obj_key_func)
    @cache_response(key_func=obj_key_func)
    def get(self, request, *args, **kwargs):
        """
        Gets a topic given by its identifier.
        ---
        responseMessages:
            - code: 404
              message: Not Found
        """
        topic = self.get_object()
        #serializer = self.get_serializer(topic)
        
        return self.retrieve(request, *args, **kwargs)

                
class PostListAPI(ListCreateAPIView):
    """
    Profile resource to list all message in a topic
    """

    list_key_func = PagingSearchListKeyConstructor()
    #serializer_class = PostSerializer


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
        responseMessages:
            - code: 400
              message: Bad Request
            - code: 401
              message: Not Authenticated
        """

        #TODO GERE les droits et l'authentification --> en cours : tester avec connection pour voir si cela fonctionne
        #TODO passer les arguments corrects a save
        author = request.user
        

        serializer = self.get_serializer_class()(data=request.data, context={'request': self.request})
        serializer.is_valid(raise_exception=True)
        topic = serializer.save(position=2,author_id=3,topic_id=1)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return PostSerializer
        elif self.request.method == 'POST':
            return PostActionSerializer


    def get_queryset(self):
        if self.request.method == 'GET':
            posts = Post.objects.filter(topic=self.kwargs.get('pk'))
        return posts
        
        
    def get_current_user(self):
        return self.request.user.profile
        
    def get_permissions(self):
        permission_classes = [AllowAny, ]
        if self.request.method == 'POST':
            permission_classes.append(DRYPermissions)
            permission_classes.append(IsAuthenticated)
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
            posts = Post.objects.filter(author=self.kwargs.get('pk'))
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

    def get_queryset(self):
        if self.request.method == 'GET':
            posts = Post.objects.filter(author=self.request.user)
        return posts


class PostDetailAPI(RetrieveUpdateAPIView):
    """
    Profile resource to display details of given message
    """
    
    queryset = Post.objects.all()
    obj_key_func = DetailKeyConstructor()
    serializer_class = PostSerializer

    @etag(obj_key_func)
    @cache_response(key_func=obj_key_func)
    def get(self, request, *args, **kwargs):
        """
        Gets a post given by its identifier.
        ---
        responseMessages:
            - code: 404
              message: Not Found
        """
        post = self.get_object()
        
        return self.retrieve(request, *args, **kwargs)



# TODO global identier quand masquer les messages
# TOD gerer l'antispam