# coding: utf-8

import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import View

from zds.member.decorator import can_write_and_read_now
from zds.utils.models import CommentLike, CommentDislike


class KarmaView(View):
    message_class = None
    list_like = False

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(self, 'oject'):
            self.object = get_object_or_404(self.message_class, pk=self.kwargs.get('pk'))
        return super(KarmaView, self).dispatch(request, *args, **kwargs)

    def get_response_object(self):
        anon_likes_id_limit = settings.LIKES_ID_LIMIT
        anon_dislikes_id_limit = settings.DISLIKES_ID_LIMIT

        resp = {
            'like': {
                'count': self.object.like,
                'user': CommentLike.objects.filter(comments__pk=self.object.pk,
                                                   user=self.request.user.pk).exists(),
            },
            'dislike': {
                'count': self.object.dislike,
                'user': CommentDislike.objects.filter(comments__pk=self.object.pk,
                                                      user=self.request.user.pk).exists(),
            }
        }

        if self.list_like:
            likes = CommentLike.objects.filter(comments__id=self.object.pk) \
                                       .filter(id__gt=anon_likes_id_limit).select_related('user')
            dislikes = CommentDislike.objects.filter(comments__id=self.object.pk) \
                                             .filter(id__gt=anon_dislikes_id_limit).select_related('user')

            resp['like']['list'] = [{'username': like.user.username,
                                     'avatarUrl': like.user.profile.get_avatar_url()} for like in likes]
            resp['dislike']['list'] = [{'username': dislike.user.username,
                                        'avatarUrl': dislike.user.profile.get_avatar_url()} for dislike in dislikes]

        return resp

    def get(self, request, *args, **kwargs):
        if request.is_ajax():
            resp = self.get_response_object()
            return HttpResponse(json.dumps(resp), content_type='application/json')

        return redirect(self.object.get_absolute_url())

    @method_decorator(login_required)
    @method_decorator(can_write_and_read_now)
    def post(self, request, *args, **kwargs):
        if request.POST.get('vote') == 'like':
            self.process_like(self.object, request.user)
        elif request.POST.get('vote') == 'dislike':
            self.process_like(self.object, request.user, add_class=CommentDislike, remove_class=CommentLike)

        if request.is_ajax():
            resp = self.get_response_object()
            return HttpResponse(json.dumps(resp), content_type='application/json')

        return redirect(self.object.get_absolute_url())

    def process_like(self, message, user,
                     add_class=CommentLike, remove_class=CommentDislike):
        if message.author.pk != user.pk:

            # Remove (dis)like if there is one
            remove_class.objects.filter(user__pk=user.pk,
                                        comments__pk=message.pk).delete()

            # Making sure the user is allowed to do that
            if not add_class.objects.filter(user__pk=user.pk,
                                            comments__pk=message.pk).exists():
                like = add_class()
                like.user = user
                like.comments = message
                like.save()
            else:
                add_class.objects.filter(user__pk=user.pk,
                                         comments__pk=message.pk).delete()

            # Recalculate (dis)like count
            message.like = CommentLike.objects.filter(comments__pk=message.pk).count()
            message.dislike = CommentDislike.objects.filter(comments__pk=message.pk).count()
            message.save()
