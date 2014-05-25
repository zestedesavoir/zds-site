# coding: utf-8

from rest_framework import serializers

from django.contrib.auth.models import User
from zds.article.models import Article
from zds.forum.models import Forum, Topic, Post
from zds.tutorial.models import Tutorial
from .fields import UnixDateField, HtmlField, ArticleArchiveLinkField

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
    create_at = UnixDateField(source = 'create_at')
    pubdate = UnixDateField(source = 'pubdate')
    update = UnixDateField(source = 'update')

    class Meta():
        model = Article
        fields = ('id', 'slug', 'title', 'description', 'authors', 
            'image', 'create_at', 'pubdate', 'update')

class ArticleSerializer(serializers.ModelSerializer):
    """
    Serializer of an article specified. We retrieve all information of the article.
    Basics information and hyperlinks to download some formats of the article like
    markdown or html.
    """
    slug = serializers.Field()
    authors = serializers.RelatedField(many = True)
    image = serializers.Field('image.url')
    archive = ArticleArchiveLinkField(source = 'archive')
    create_at = UnixDateField(source = 'create_at')
    pubdate = UnixDateField(source = 'pubdate')
    update = UnixDateField(source = 'update')

    class Meta():
        model = Article
        fields = ('id', 'slug', 'title', 'description', 'authors', 'image', 
            'is_locked', 'is_visible', 'archive', 'create_at', 'pubdate', 'update')
        

class ForumSerializer(serializers.ModelSerializer):
    slug = serializers.Field()

    class Meta:
        model = Forum
        fields = ('id', 'title', 'subtitle', 'slug')

class TopicSerializer(serializers.ModelSerializer):
    author = serializers.Field(source='author.username')
    pubdate = UnixDateField(source = 'pubdate')

    class Meta:
        model = Topic
        fields = ('id', 'title', 'subtitle', 'forum', 'author',
                  'pubdate', 'is_solved', 'is_locked', 'is_sticky')

class PostSerializer(serializers.ModelSerializer):
    author = serializers.Field(source='author.username')
    update = UnixDateField(source = 'update')

    class Meta:
        model = Post
        fields = ('id', 'text', 'topic', 'author', 'pubdate', 'update')

class TutorialSerializer(serializers.ModelSerializer):
    slug = serializers.Field()
    authors = serializers.RelatedField(many = True)
    image = serializers.Field('image.url')
    create_at = UnixDateField(source = 'create_at')
    pubdate = UnixDateField(source = 'pubdate')
    update = UnixDateField(source = 'update')
    html = HtmlField(source = 'id')

    class Meta:
        model = Tutorial
        fields = ('id', 'slug', 'title', 'description', 'image', 
            'is_locked', 'create_at', 'pubdate', 'update', 'html')
