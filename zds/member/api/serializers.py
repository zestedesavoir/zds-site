# -*- coding: utf-8 -*-

import os

from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers

from zds.member.models import Profile
from zds.settings import SITE_ROOT


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


class ProfileUpdateSerializer(serializers.ModelSerializer):
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

        instance.user.username = validated_data.get('user').get('username', instance.user.username)
        instance.user.email = validated_data.get('user').get('email', instance.user.email)
        instance.site = validated_data.get('site', instance.site)
        instance.avatar_url = validated_data.get('avatar_url', instance.avatar_url)
        instance.biography = validated_data.get('biography', instance.biography)
        instance.sign = validated_data.get('sign', instance.sign)
        instance.show_email = validated_data.get('show_email', instance.show_email)
        instance.show_sign = validated_data.get('show_sign', instance.show_sign)
        instance.hover_or_click = validated_data.get('hover_or_click', instance.hover_or_click)
        instance.email_for_answer = validated_data.get('email_for_answer', instance.email_for_answer)
        instance.user.save()
        instance.save()
        return instance

    def validate_username(self, value):
        """
        Checks about the username.
        """

        msg = None
        if value:
            if value.strip() == '':
                msg = _(u'Le nom d\'utilisateur ne peut-être vide')
            elif User.objects.filter(username=value).count() > 0:
                msg = _(u'Ce nom d\'utilisateur est déjà utilisé')
            # Forbid the use of comma in the username
            elif "," in value:
                msg = _(u'Le nom d\'utilisateur ne peut contenir de virgules')
            elif value != value.strip():
                msg = _(u'Le nom d\'utilisateur ne peut commencer/finir par des espaces')
            if msg is not None:
                raise serializers.ValidationError(msg)
            return value
        return self.instance.user.username

    def validate_email(self, value):
        """
        Checks about the email.
        """

        if value:
            msg = None
            # Chech if email provider is authorized
            with open(os.path.join(SITE_ROOT, 'forbidden_email_providers.txt'), 'r') as fh:
                for provider in fh:
                    if provider.strip() in value:
                        msg = _(u'Utilisez un autre fournisseur d\'adresses courriel.')
                        break

            # Check that the email is unique
            if User.objects.filter(email=value).count() > 0:
                msg = _(u'Votre adresse courriel est déjà utilisée')
            if msg is not None:
                raise serializers.ValidationError(msg)
            return value
        return self.instance.user.email
