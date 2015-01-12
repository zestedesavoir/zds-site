# -*- coding: utf-8 -*-

from django.contrib.auth.models import User

from rest_framework import serializers

from zds.member.commons import ProfileUsernameValidator, ProfileEmailValidator, \
    ProfileCreate
from zds.member.models import Profile


class UserSerializer(serializers.ModelSerializer):
    """
    Serializers of a user object.
    """

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'is_active', 'date_joined')


class UserCreateSerializer(serializers.ModelSerializer, ProfileCreate, ProfileUsernameValidator, ProfileEmailValidator):
    """
    Serializers of a user object to create one.
    """

    class Meta:
        model = User
        fields = ('username', 'email', 'password')
        write_only_fields = ('password')

    def create(self, validated_data):
        profile = self.create_profile(validated_data)
        self.save_profile(profile)
        return profile.user

    def throw_error(self, key=None, message=None):
        raise serializers.ValidationError(message)


class ProfileSerializer(serializers.ModelSerializer):
    """
    Serializers of a profile object.
    """

    id = serializers.ReadOnlyField(source='user.id')
    username = serializers.CharField(source='user.username')
    email = serializers.EmailField(source='user.email')
    is_active = serializers.BooleanField(source='user.is_active')
    date_joined = serializers.DateTimeField(source='user.date_joined')

    class Meta:
        model = Profile
        fields = ('id', 'username', 'show_email', 'email', 'is_active',
                  'site', 'avatar_url', 'biography', 'sign', 'email_for_answer',
                  'last_visit', 'date_joined')


class ProfileValidatorSerializer(serializers.ModelSerializer, ProfileUsernameValidator, ProfileEmailValidator):
    """
    Serializers of a profile object used to update a member.
    """

    username = serializers.CharField(source='user.username', required=False, allow_blank=True)
    email = serializers.EmailField(source='user.email', required=False, allow_blank=True)

    class Meta:
        model = Profile
        fields = ('username', 'email', 'site', 'avatar_url', 'biography',
                  'sign', 'show_email', 'show_sign', 'hover_or_click',
                  'email_for_answer')

    def update(self, instance, validated_data):
        """
        Update and return an existing `Profile` instance, given the validated data.
        """
        instance.user.username = validated_data.get('user').get('username', instance.user.username) or instance.user.username
        instance.user.email = validated_data.get('user').get('email', instance.user.email) or instance.user.email
        instance.site = validated_data.get('site', instance.site) or instance.site
        instance.avatar_url = validated_data.get('avatar_url', instance.avatar_url) or instance.avatar_url
        instance.biography = validated_data.get('biography', instance.biography) or instance.biography
        instance.sign = validated_data.get('sign', instance.sign) or instance.sign
        instance.show_email = validated_data.get('show_email', instance.show_email) or instance.show_email
        instance.show_sign = validated_data.get('show_sign', instance.show_sign) or instance.show_sign
        instance.hover_or_click = validated_data.get('hover_or_click', instance.hover_or_click) or instance.hover_or_click
        instance.email_for_answer = validated_data.get('email_for_answer', instance.email_for_answer) or instance.email_for_answer
        instance.user.save()
        instance.save()
        return instance

    def throw_error(self, key=None, message=None):
        raise serializers.ValidationError(message)


class ProfileSanctionSerializer(serializers.ModelSerializer):
    """
    Serializers of a profile object to set the user in reading only access.
    """

    username = serializers.CharField(source='user.username', required=False, allow_blank=True)
    email = serializers.EmailField(source='user.email', required=False, allow_blank=True)

    class Meta:
        model = Profile
        fields = ('id', 'username', 'email', 'can_write', 'end_ban_write', 'can_read', 'end_ban_read')
