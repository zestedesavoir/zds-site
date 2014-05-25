# coding: utf-8

from django.contrib.auth.models import User

from rest_framework import generics

from .serializers import UserSerializer, ArticleListSerializer, ArticleSerializer,\
    ForumSerializer, TopicSerializer, PostSerializer, TutorialSerializer

from zds.article.models import Article, get_last_articles
from zds.tutorial.models import get_last_tutorials
from zds.forum.models import Forum, Topic, Post

class UserList(generics.ListAPIView):
    '''List all users.'''
    queryset = User.objects.all()
    serializer_class = UserSerializer

class UserDetail(generics.RetrieveAPIView):
    '''Detail of a user given.'''
    queryset = User.objects.all()
    serializer_class = UserSerializer

class ArticlePublishedList(generics.ListAPIView):
    '''List all published articles.'''
    queryset = get_last_articles()
    serializer_class = ArticleListSerializer

class ArticlePublishedDetail(generics.RetrieveAPIView):
    '''Detail of an article given.'''
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer

class ForumList(generics.ListAPIView):
    '''List all forums.'''
    queryset = Forum.objects.all()
    serializer_class = ForumSerializer

class TopicList(generics.ListAPIView):
    '''List all topics.'''
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer

class PostList(generics.ListAPIView):
    '''List all posts.'''
    queryset = Post.objects.all()
    serializer_class = PostSerializer

class TutorialPublishedList(generics.ListAPIView):
    '''List all published tutorials.'''
    queryset = get_last_tutorials()
    serializer_class = TutorialSerializer