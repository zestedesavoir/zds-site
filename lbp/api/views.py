from datetime import datetime

from django.shortcuts import redirect, get_object_or_404

from django.db.models import Q
from django.http import Http404
from django.http import HttpResponse

from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

from lbp.utils import render_template, slugify
from lbp.utils.paginator import paginator_range

from lbp.forum.models import Category, Forum, Topic, Post, TopicRead, TopicFollowed, POSTS_PER_PAGE, TOPICS_PER_PAGE

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import mixins, generics, permissions, status

from serializers import CategorySerializer, ForumSerializer, TopicSerializer, TopicFollowedSerializer, TopicReadSerializer, PostSerializer, UserSerializer
from permissions import IsOwnerOrReadOnly

import django_filters

class UserList(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class UserDetail(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class CategoryList(generics.ListAPIView):
    """
    List all category
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class CategoryDetail(generics.RetrieveAPIView):
    """
    Retrieve a Category.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


class ForumFilter(django_filters.FilterSet):
    class Meta:
        model = Forum
        fields = ['category']

class ForumList(generics.ListAPIView):
    """
    List all forum.
    """
    queryset = Forum.objects.all()
    serializer_class = ForumSerializer
    filter_class = ForumFilter

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class ForumDetail(generics.RetrieveAPIView):
    """
    Retrieve a Forum.
    """
    queryset = Forum.objects.all()
    serializer_class = ForumSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

class TopicReadFilter(django_filters.FilterSet):
    class Meta:
        model = TopicRead
        fields = ['user']

class TopicReadList(generics.ListCreateAPIView):
    """
    List all Topic read, or create a new topic read.
    """
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    queryset = TopicRead.objects.all()
    serializer_class = TopicReadSerializer
    filter_class = TopicReadFilter

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def pre_save(self, obj):
        obj.user = self.request.user

class TopicReadDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a Topic read.
    """
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly,)
    queryset = TopicRead.objects.all()
    serializer_class = TopicReadSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

    def pre_save(self, obj):
        obj.user = self.request.user

class TopicFollowedFilter(django_filters.FilterSet):
    class Meta:
        model = TopicFollowed
        fields = ['user']

class TopicFollowedList(generics.ListCreateAPIView):
    """
    List all Topic followed, or create a new topic followed.
    """
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    queryset = TopicFollowed.objects.all()
    serializer_class = TopicFollowedSerializer
    filter_class = TopicFollowedFilter

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def pre_save(self, obj):
        obj.user = self.request.user

class TopicFollowedDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a Topic followed.
    """
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly,)
    queryset = TopicRead.objects.all()
    serializer_class = TopicFollowedSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

    def pre_save(self, obj):
        obj.user = self.request.user

class TopicFilter(django_filters.FilterSet):
    is_solved = django_filters.BooleanFilter()
    is_locked = django_filters.BooleanFilter()
    is_sticky = django_filters.BooleanFilter()
    class Meta:
        model = Topic
        fields = ['author', 'forum', 'is_solved', 'is_locked', 'is_sticky']

class TopicList(generics.ListCreateAPIView):
    """
    List all Topic, or create a new topic.
    """
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer
    filter_class = TopicFilter

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def pre_save(self, obj):
        obj.author = self.request.user
        lst= Post.objects.all().filter(topic=obj).order_by('-pubdate') 
        if  len(lst) > 0:
            obj.last_message = lst[0]

    def post_save(self, obj, created=True):
        # if i create a topic, i follow it
        tf = TopicFollowed(topic=obj, user=self.request.user)
        tf.save();

class TopicDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a Topic.
    """
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly,)
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

    def pre_save(self, obj):
        obj.author = self.request.user
        lst= Post.objects.all().filter(topic=obj).order_by('-pubdate') 
        if  len(lst) > 0:
            obj.last_message = lst[0]
    
    def post_save(self, obj, created=True):
        # if i create a topic, i follow it
        tf = TopicFollowed(topic=obj, user=self.request.user)
        tf.save();

class PostFilter(django_filters.FilterSet):
    position_in_topic = django_filters.NumberFilter()
    class Meta:
        model = Post
        fields = ['author', 'topic', 'position_in_topic']

class PostList(generics.ListCreateAPIView):
    """
    List all Post, or create a new post.
    """
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    filter_class = PostFilter

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def pre_save(self, obj):
        obj.author = self.request.user
        if not obj.position_in_topic :
            obj.position_in_topic = obj.topic.get_post_count()+1
        else:
            obj.update = datetime.now()        
    
    #update the last message after post
    def post_save(self, obj, created=True):
        if not obj.update :
            tp=Topic.objects.all().get(pk=obj.topic.pk)
            tp.last_message = obj
            tp.save()

class PostDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a Post.
    """
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly,)
    queryset = Post.objects.all()
    serializer_class = PostSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

    def pre_save(self, obj):
        obj.author = self.request.user
        if not obj.position_in_topic :
            obj.position_in_topic = obj.topic.get_post_count()+1
            
        else:
            obj.update = datetime.now()
    
    #update the last message after post
    def post_save(self, obj, created=True):
        if not obj.update :
            tp=Topic.objects.all().get(pk=obj.topic.pk)
            tp.last_message = obj
            tp.save()
