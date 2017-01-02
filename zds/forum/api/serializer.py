from rest_framework import serializers
from zds.forum.models import Forum, Topic, Post
from zds.utils.models import Alert
from dry_rest_permissions.generics import DRYPermissionsField
from dry_rest_permissions.generics import DRYPermissions
from django.shortcuts import get_object_or_404
from zds.utils.validators import TitleValidator, TextValidator


class ForumSerializer(serializers.ModelSerializer):
    class Meta:
        model = Forum

class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        #fields = ('id', 'title', 'subtitle', 'slug', 'category', 'position_in_category')
        permissions_classes = DRYPermissions



class TopicCreateSerializer(serializers.ModelSerializer, TitleValidator, TextValidator):
    """
    Serializer to create a new topic.
    """
    text = serializers.CharField() 
    permissions = DRYPermissionsField()

    class Meta:
        model = Topic
        fields = ('id', 'title', 'subtitle', 'forum', 'text',
                  'author', 'last_message', 'pubdate',
                  'permissions', 'slug')
        read_only_fields = ('id', 'author', 'last_message', 'pubdate', 'permissions', 'slug')

    def create(self, validated_data):
        
        # Remember that text ist not a field for a Topic but for a post.
        text = validated_data.pop('text')
        new_topic = Topic.objects.create(**validated_data)
        
        # Instead we use text here.
        first_message = Post.objects.create(topic=new_topic,text=text,position=0,author=new_topic.author)
        new_topic.last_message = first_message
        new_topic.save()
        
        # And serve it here so it appears in response.
        new_topic.text = text
        return new_topic


class TopicUpdateSerializer(serializers.ModelSerializer, TitleValidator, TextValidator):
    """
    Serializer to update a topic.
    """
    title = serializers.CharField(required=False, allow_blank=True)
    subtitle = serializers.CharField(required=False, allow_blank=True)
    permissions = DRYPermissionsField()

    class Meta:
        model = Topic
        fields = ('id', 'title', 'subtitle', 'permissions', 'forum', 'is_locked', 'is_solved', 'tags')
        read_only_fields = ('id', 'permissions', 'forum', 'is_locked')
# Todo : lors de l'update on a le droit de mettre un titre vide ? 
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
        
    def throw_error(self, key=None, message=None):
        raise serializers.ValidationError(message)
        
class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        exclude = ('ip_address', 'text_hidden',)
        read_only = ('ip_address', 'text_hidden',)
        permissions_classes = DRYPermissions

class PostCreateSerializer(serializers.ModelSerializer, TextValidator):
    """
    Serializer to send a post in a topic
    """
    permissions = DRYPermissionsField()

    class Meta:
        model = Post
        fields = ('id', 'text', 'text_html', 'permissions')
        read_only_fields = ('text_html', 'permissions')
    # TODO a voir quel champ en read only

    def create(self, validated_data):
        # Get topic
        pk_topic = validated_data.get('topic_id')
        topic = get_object_or_404(Topic, pk=(pk_topic))
        new_post = Post.objects.create(**validated_data)
        return new_post

    # Todo a t on besoin d'un validateur
    #def throw_error(self, key=None, message=None):
        #raise serializers.ValidationError(message)

class PostUpdateSerializer(serializers.ModelSerializer, TextValidator):
    """
    Serializer to update a post.
    """
    text = serializers.CharField(required=True, allow_blank=True)
    permissions = DRYPermissionsField()

    class Meta:
        model = Topic
        fields = ('id', 'text', 'permissions',)
        read_only_fields = ('id', 'permissions',)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
        

class AlertSerializer(serializers.ModelSerializer):
    """
    Serializer to alert a post.
    """
    permissions = DRYPermissionsField()

    class Meta:
        model = Alert
        fields = ('id', 'text', 'permissions',)
        read_only_fields = ('permissions',)


    def create(self, validated_data):
        # Get topic TODO pourquoi ces lignes?
        pk_post = validated_data.get('comment')
        post = get_object_or_404(Post, pk=(pk_post))
        alert = Alert.objects.create(**validated_data)
        return alert

    # Todo a t on besoin d'un validateur ?
    #def throw_error(self, key=None, message=None):
        #raise serializers.ValidationError(message)