# -*- coding: utf-8 -*-

from rest_framework import serializers

from zds.mp.models import PrivateTopic


class PrivateTopicListSerializer(serializers.ModelSerializer):
    """
    Serializers of a private topic object.
    """

    class Meta:
        model = PrivateTopic
