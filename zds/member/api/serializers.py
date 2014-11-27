# -*- coding: utf-8 -*-

from django.contrib.auth.models import User
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    """
    Serializers of a user object.
    """
    class Meta:
        model = User
        fields = ('username', 'email', 'is_staff')
