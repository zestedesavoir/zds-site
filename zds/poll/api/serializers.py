from rest_framework import serializers

from zds.poll.models import Poll

class PollListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Poll
        fields = ('id', 'title')


class PollDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = Poll
        fields = ('id', 'title')