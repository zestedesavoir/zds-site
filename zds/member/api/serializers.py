# -*- coding: utf-8 -*-

from django.contrib.auth.models import User

from rest_framework import serializers

from zds.member.models import Profile


class UserSerializer(serializers.ModelSerializer):
    """
    Serializers of a user object.
    """

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'is_active', 'date_joined')


class ProfileSerializer(serializers.ModelSerializer):
    """
    Serializers of a profile object.
    """
    id = serializers.Field(source='user.id')
    username = serializers.CharField(source='user.username')
    email = serializers.EmailField(source='user.email')
    is_active = serializers.BooleanField(source='user.is_active')
    date_joined = serializers.DateField(source='user.date_joined')

    class Meta:
        model = Profile
        fields = ('id', 'username', 'show_email', 'email', 'is_active',
                  'site', 'avatar_url', 'biography', 'sign', 'email_for_answer',
                  'last_visit', 'date_joined')
