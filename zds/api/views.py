# coding: utf-8

from django.contrib.auth.models import User

from rest_framework import generics

from .serializers import UserSerializer, ArticleSerializer, ForumSerializer,\
    TopicSerializer, PostSerializer

from zds.article.models import get_last_articles
from zds.forum.models import Forum, Topic, Post

class UserList(generics.ListAPIView):
    '''List all users'''
    queryset = User.objects.all()
    serializer_class = UserSerializer

class UserDetail(generics.RetrieveAPIView):
    '''Detail of a user given'''
    queryset = User.objects.all()
    serializer_class = UserSerializer

class ArticlePublishedList(generics.ListAPIView):
    '''List all published articles'''
    queryset = get_last_articles()
    serializer_class = ArticleSerializer

class ForumList(generics.ListAPIView):
    '''List all forums'''
    queryset = Forum.objects.all()
    serializer_class = ForumSerializer

class TopicList(generics.ListAPIView):
    '''List all topics'''
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer

class PostList(generics.ListAPIView):
    '''List all posts'''
    queryset = Post.objects.all()
    serializer_class = PostSerializer