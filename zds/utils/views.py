# coding: utf-8

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response

from zds.member.decorator import can_write_and_read_now
from zds.utils.models import CommentVote


class KarmaView(APIView):
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
        resp = {
            'like': {
                'count': self.object.like,
                'list': [{'username': vote.user.username, 'link': vote.user.get_absolute_url(),
                          'avatarUrl': vote.user.profile.get_avatar_url()} for vote in votes if vote.positive]
            },
            'dislike': {
                'count': self.object.dislike,
                'list': [{'username': vote.user.username, 'link': vote.user.get_absolute_url(),
                          'avatarUrl': vote.user.profile.get_avatar_url()} for vote in votes if not vote.positive]
            },
            'user': user_vote
        }

        return resp

    def get(self, request, *args, **kwargs):
        resp = self.get_response_object()
        return Response(resp)

    @method_decorator(login_required)
    @method_decorator(can_write_and_read_now)
    def post(self, request, *args, **kwargs):
        if self.object.author.pk != request.user.pk:
            vote = request.POST.get('vote')
            if vote == 'neutral':
                CommentVote.objects.filter(user=request.user, comment=self.object).delete()
            elif vote in ['like', 'dislike']:
                CommentVote.objects.update_or_create(user=request.user, comment=self.object,
                                                     defaults={'positive': (vote == 'like')})
            else:
                return Response({'error': 'parameter \'vote\' is not valid'}, status=400)
        else:
            return Response({'error': 'author can\'t vote his own post'}, status=401)

        self.object.like = CommentVote.objects.filter(positive=True, comment=self.object).count()
        self.object.dislike = CommentVote.objects.filter(positive=False, comment=self.object).count()
        self.object.save()

        if request.is_ajax():
            resp = self.get_response_object()
            return Response(resp)

        return redirect(self.object.get_absolute_url())
