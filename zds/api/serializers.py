# coding: utf-8

from rest_framework import serializers

from django.contrib.auth.models import User
from zds.article.models import Article
from zds.forum.models import Forum, Topic, Post

class UnixDateField(serializers.DateTimeField):
    def to_native(self, value):
        """ Return timestamp for a datetime object or None"""
        import time
        try:
            return int(time.mktime(value.timetuple()))
        except (AttributeError, TypeError):
            return None

    def from_native(self, value):
        import datetime
        return datetime.datetime.fromtimestamp(int(value))

class UserSerializer(serializers.ModelSerializer):
    articles = serializers.PrimaryKeyRelatedField(many=True, read_only='true')
    comments = serializers.PrimaryKeyRelatedField(many=True, read_only='true')

    class Meta:
        model = User
        fields = ('id', 'username', 'articles', 'comments')

class ArticleSerializer(serializers.ModelSerializer):
    slug = serializers.Field()
    authors = serializers.RelatedField(many = True)
    image = serializers.Field('image.url')
    create_at = UnixDateField(source = 'create_at')
    pubdate = UnixDateField(source = 'pubdate')
    update = UnixDateField(source = 'update')

    class Meta():
        model = Article
        fields = ('id', 'slug', 'title', 'description', 'authors', 
            'image', 'is_locked', 'create_at', 'pubdate', 'update')

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
