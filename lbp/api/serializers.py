from django.forms import widgets
from django.contrib.auth.models import User
from rest_framework import serializers
from lbp.forum.models import Category, Forum, Topic, Post, TopicRead, TopicFollowed


class CategorySerializer(serializers.ModelSerializer):
    slug = serializers.Field()
    class Meta:
        model = Category
        fields = ('id', 'title', 'position', 'slug')

class ForumSerializer(serializers.ModelSerializer):
    slug = serializers.Field()
    class Meta:
        model = Forum
        fields = ('id', 'title', 'subtitle', 'category', 'position_in_category', 'slug')

class TopicReadSerializer(serializers.ModelSerializer):
    user = serializers.Field(source='user.username')
    class Meta:
        model = TopicRead
        fields = ('id', 'topic', 'post', 'user')

class TopicFollowedSerializer(serializers.ModelSerializer):
    user = serializers.Field(source='user.username')
    class Meta:
        model = TopicFollowed
        fields = ('id', 'topic', 'user')

class TopicSerializer(serializers.ModelSerializer):
    author = serializers.Field(source='author.username')
    is_locked = serializers.Field()
    is_solved = serializers.Field()
    is_sticky = serializers.Field()
    last_message = serializers.Field()
    class Meta:
        model = Topic
        fields = ('id', 'title', 'subtitle', 'forum', 'author', 'last_message', 'pubdate', 'is_solved', 'is_locked', 'is_sticky')

class PostSerializer(serializers.ModelSerializer):
    author = serializers.Field(source='author.username')
    update = serializers.Field()
    position_in_topic = serializers.Field()
    class Meta:
        model = Post
        fields = ('id', 'text', 'topic', 'author', 'pubdate', 'update', 'position_in_topic')

class UserSerializer(serializers.ModelSerializer):
    topics = serializers.PrimaryKeyRelatedField(many=True, read_only='true')
    articles = serializers.PrimaryKeyRelatedField(many=True, read_only='true')
    topics_read = serializers.PrimaryKeyRelatedField(many=True, read_only='true')
    topics_followed = serializers.PrimaryKeyRelatedField(many=True, read_only='true')
    posts = serializers.PrimaryKeyRelatedField(many=True, read_only='true')
    class Meta:
        model = User
        fields = ('id', 'username','topics', 'posts', 'topics_read', 'topics_followed', 'articles')
