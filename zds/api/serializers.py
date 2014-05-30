# coding: utf-8

from rest_framework import serializers

from django.contrib.auth.models import User
from zds.article.models import Article
from zds.forum.models import Category, Forum, Topic, Post
from zds.tutorial.models import Tutorial
from .fields import UnixDateField, TutorialHtmlField, ArticleArchiveLinkField

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer of an user. We retrieve all these information on the website like
    tutorials, articles and posts on forums.
    """
    tutorials = serializers.PrimaryKeyRelatedField(many=True, read_only='true')
    articles = serializers.PrimaryKeyRelatedField(many=True, read_only='true')
    comments = serializers.PrimaryKeyRelatedField(many=True, read_only='true')

    class Meta:
        model = User
        fields = ('id', 'username', 'tutorials', 'articles', 'comments')

class ArticleListSerializer(serializers.ModelSerializer):
    """
    Serializer of articles. We retrieve some importants information about
    articles. If the user would like to know more about one of these articles,
    he must to call another api to retrieve details.
    """
    slug = serializers.Field()
    authors = serializers.RelatedField(many = True)
    image = serializers.Field('image.url')
    pubdate = UnixDateField(source = 'pubdate')

    class Meta():
        model = Article
        fields = ('id', 'slug', 'title', 'description', 'authors',  'image', 'pubdate')

class ArticleSerializer(serializers.ModelSerializer):
    """
    Serializer of an article specified. We retrieve all information of the article.
    Basics information and hyperlinks to download some formats of the article like
    markdown or html.
    """
    slug = serializers.Field()
    authors = serializers.RelatedField(many = True)
    image = serializers.Field('image.url')
    archive = ArticleArchiveLinkField(source = 'id')
    create_at = UnixDateField(source = 'create_at')
    pubdate = UnixDateField(source = 'pubdate')
    update = UnixDateField(source = 'update')

    class Meta():
        model = Article
        fields = ('id', 'slug', 'title', 'description', 'authors', 'image', 
            'is_locked', 'is_visible', 'archive', 'create_at', 'pubdate', 'update')

class TutorialListSerializer(serializers.ModelSerializer):
    """
    Serializer of tutorials. We retrieve some importants information about
    tutorials. If the user would like to know more about one of these tutorials,
    he must to call another api to retrieve details.
    """
    slug = serializers.Field()
    authors = serializers.RelatedField(many = True)
    image = serializers.Field('image.url')
    pubdate = UnixDateField(source = 'pubdate')

    class Meta:
        model = Tutorial
        fields = ('id', 'slug', 'title', 'description', 'authors', 'image', 'pubdate')
        

class TutorialSerializer(serializers.ModelSerializer):
    """
    Serializer of a tutorial specified. We retrieve all information of the tutorial.
    Basics information and hyperlinks to download some formats of the tutorial like
    markdown or html.
    """
    slug = serializers.Field()
    authors = serializers.RelatedField(many = True)
    image = serializers.Field('image.url')
    create_at = UnixDateField(source = 'create_at')
    pubdate = UnixDateField(source = 'pubdate')
    update = UnixDateField(source = 'update')
    html = TutorialHtmlField(source = 'id')

    class Meta:
        model = Tutorial
        fields = ('id', 'slug', 'title', 'description', 'authors','image', 
            'is_locked', 'create_at', 'pubdate', 'update', 'html')

class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for categories. We retrieve all information about categories.
    """
    slug = serializers.Field()

    class Meta:
        model = Category
        fields = ('id', 'title', 'position', 'slug')

class ForumSerializer(serializers.ModelSerializer):
    """
    Serializer for forums. We retrieve all information about forums.
    """
    slug = serializers.Field()
    image = serializers.Field('image.url')

    class Meta:
        model = Forum
        fields = ('id', 'title', 'subtitle', 'slug', 'category')

class TopicSerializer(serializers.ModelSerializer):
    """
    Serializer for topics. We retrieve all information about topics.
    """
    author = serializers.Field(source='author.username')
    pubdate = UnixDateField(source = 'pubdate')

    class Meta:
        model = Topic
        fields = ('id', 'title', 'subtitle', 'forum', 'author', 'pubdate', 
            'is_solved', 'is_locked', 'is_sticky')

class PostSerializer(serializers.ModelSerializer):
    """
    Serializer for posts. We retrieve all information about posts.
    """
    author = serializers.Field(source='author.username')
    update = UnixDateField(source = 'update')

    class Meta:
        model = Post
        fields = ('id', 'text', 'topic', 'author', 'pubdate', 'update')
