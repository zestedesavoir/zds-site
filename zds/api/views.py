# coding: utf-8

from django.contrib.auth.models import User

from rest_framework import generics

from .serializers import UserSerializer, ArticleListSerializer, ArticleSerializer,\
    TutorialListSerializer, TutorialSerializer, CategorySerializer, ForumSerializer,\
    TopicSerializer, PostSerializer

from zds.article.models import Article, get_last_articles
from zds.tutorial.models import Tutorial, get_last_tutorials
from zds.forum.models import Category, Forum, Topic, Post

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

class TutorialPublishedList(generics.ListAPIView):
    '''List all published tutorials.'''
    queryset = get_last_tutorials()
    serializer_class = TutorialListSerializer

class TutorialPublishedDetail(generics.RetrieveAPIView):
    '''Detail of a tutorial given'''
    queryset = Tutorial.objects.all()
    serializer_class = TutorialSerializer

class ForumList(generics.ListAPIView):
    '''List all forums.'''
    queryset = Forum.objects.all()
    serializer_class = ForumSerializer

class CategoryList(generics.ListAPIView):
    '''List all categories.'''
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class TopicList(generics.ListAPIView):
    '''List all topics.'''
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer

class PostList(generics.ListAPIView):
    '''List all posts.'''
    queryset = Post.objects.all()
    serializer_class = PostSerializer