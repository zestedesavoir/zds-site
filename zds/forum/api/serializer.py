from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from zds.forum.models import Forum, Topic, Post
from zds.utils.models import Alert
from dry_rest_permissions.generics import DRYPermissionsField
from dry_rest_permissions.generics import DRYPermissions
from django.shortcuts import get_object_or_404


class ForumSerializer(ModelSerializer):
    class Meta:
        model = Forum
        permissions_classes = DRYPermissions


class TopicSerializer(ModelSerializer):
    class Meta:
        model = Topic
        #fields = ('id', 'title', 'subtitle', 'slug', 'category', 'position_in_category')
        permissions_classes = DRYPermissions


# Idem renommer TODO
class TopicActionSerializer(ModelSerializer):
    """
    Serializer to create a new topic.
    """
    text = serializers.SerializerMethodField() 
    permissions = DRYPermissionsField()

    class Meta:
        model = Topic
        fields = ('id', 'title', 'subtitle', 'text', 'forum',
                  'author', 'last_message', 'pubdate',
                  'permissions', 'slug')
        read_only_fields = ('id', 'author', 'last_message', 'pubdate', 'permissions')
# TODO je pense qu'avec cette config on peut deplacer un sujet en tant qu'user
# TODO le text deconne    
    def create(self, validated_data):
        
        text = self._fields.pop('text')
        new_topic = Topic.objects.create(**validated_data)
        first_message = Post.objects.create(topic=new_topic,text=text,position=0,author=new_topic.author)
        new_topic.last_message = first_message
        new_topic.save()
        return new_topic
"""

    def create(self, validated_data):
        # This hack is necessary because `text` isn't a field of PrivateTopic.
        self._fields.pop('text')
        return send_mp(self.context.get('request').user,
                       validated_data.get('participants'),
                       validated_data.get('title'),
                       validated_data.get('subtitle') or '',
                       validated_data.get('text'),
                       True,
                       False)
""" 

class TopicUpdateSerializer(ModelSerializer):
    """
    Serializer to update a topic.
    """
    can_be_empty = True # TODO verifier l'interet de cette ligne
    title = serializers.CharField(required=False, allow_blank=True)
    subtitle = serializers.CharField(required=False, allow_blank=True)
    # TODO ajouter les tag et la resolution
    permissions = DRYPermissionsField()

    class Meta:
        model = Topic
        fields = ('id', 'title', 'subtitle', 'permissions',)
        read_only_fields = ('id', 'permissions',)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class PostSerializer(ModelSerializer):
    class Meta:
        model = Post
        #fields = ('id', 'title', 'subtitle', 'slug', 'category', 'position_in_category')
        permissions_classes = DRYPermissions

# TODO renommer
class PostActionSerializer(ModelSerializer):
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
        Post.objects.create(**validated_data)
        return topic.last_message

    # Todo a t on besoin d'un validateur
    #def throw_error(self, key=None, message=None):
        #raise serializers.ValidationError(message)

class PostUpdateSerializer(ModelSerializer):
    """
    Serializer to update a post.
    """
    can_be_empty = True # TODO verifier l'interet de cette ligne
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
        

class AlertSerializer(ModelSerializer):
    """
    Serializer to alert a post.
    """
    permissions = DRYPermissionsField()

    class Meta:
        model = Alert
        fields = ('id', 'text', 'permissions',)
        read_only_fields = ('permissions',)


    def create(self, validated_data):
        # Get topic
        pk_post = validated_data.get('comment')
        post = get_object_or_404(Post, pk=(pk_post))
        Alert.objects.create(**validated_data)
        return topic.last_message

    # Todo a t on besoin d'un validateur
    #def throw_error(self, key=None, message=None):
        #raise serializers.ValidationError(message)