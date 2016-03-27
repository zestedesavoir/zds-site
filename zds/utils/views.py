# coding: utf-8

from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from zds.member.api.serializers import UserListSerializer
from zds.member.api.permissions import CanReadAndWriteNowOrReadOnly
from zds.utils.models import CommentVote


class KarmaView(APIView):
    permission_classes = (IsAuthenticatedOrReadOnly, CanReadAndWriteNowOrReadOnly,)
    message_class = None

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(self, 'object'):
            self.object = get_object_or_404(self.message_class, pk=self.kwargs.get('pk'))
        return super(KarmaView, self).dispatch(request, *args, **kwargs)

    def get_response_object(self):
        anon_id_limit = settings.VOTES_ID_LIMIT

        if(self.request.user.is_authenticated()):
            try:
                user_vote = 'like' if CommentVote.objects.get(user=self.request.user,
                                                              comment=self.object).positive else 'dislike'
            except CommentVote.DoesNotExist:
                user_vote = 'neutral'
        else:
            user_vote = 'neutral'

        votes = CommentVote.objects.filter(comment=self.object, id__gt=anon_id_limit).select_related('user').all()
        like_list = UserListSerializer([vote.user for vote in votes if vote.positive], many=True)
        dislike_list = UserListSerializer([vote.user for vote in votes if not vote.positive], many=True)

        resp = {
            'like': {
                'count': self.object.like,
                'list': like_list.data
            },
            'dislike': {
                'count': self.object.dislike,
                'list': dislike_list.data
            },
            'user': user_vote
        }

        return resp

    def get(self, request, *args, **kwargs):
        resp = self.get_response_object()
        return Response(resp)

    def post(self, request, *args, **kwargs):
        if self.object.author.pk == request.user.pk:
            raise PermissionDenied(detail='author can\'t vote his own post')

        vote = request.POST.get('vote')
        if vote == 'neutral':
            CommentVote.objects.filter(user=request.user, comment=self.object).delete()
        elif vote in ['like', 'dislike']:
            CommentVote.objects.update_or_create(user=request.user, comment=self.object,
                                                 defaults={'positive': (vote == 'like')})
        else:
            raise ValidationError(detail='parameter \'vote\' is not valid')

        self.object.like = CommentVote.objects.filter(positive=True, comment=self.object).count()
        self.object.dislike = CommentVote.objects.filter(positive=False, comment=self.object).count()
        self.object.save()

        resp = self.get_response_object()
        return Response(resp)
