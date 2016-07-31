#!/usr/bin/python
# -*- coding: utf-8 -*-

from rest_framework import serializers

from zds.poll.models import Poll, Choice


class ChoiceSerializer(serializers.ModelSerializer):

    votes = serializers.IntegerField(source='get_count_votes')

    class Meta:
        model = Choice
        fields = ('pk', 'choice', 'votes')


class PollDetailSerializer(serializers.ModelSerializer):

    choices = ChoiceSerializer(many=True)

    class Meta:
        model = Poll
        fields = ('pk', 'title', 'anonymous_vote', 'type_vote', 'pubdate', 'enddate', 'choices')


class VoteSerializer(serializers.Serializer):

    def update(self, instance, validated_data):
        request = self.context.get('request', None)
        choice_pk = request.data['choice']
        choice = Choice.objects.get(pk=choice_pk)
        choice.set_user_vote(request.user)

        instance.save()
        return instance
