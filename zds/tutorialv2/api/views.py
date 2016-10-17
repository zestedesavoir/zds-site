# coding: utf-8
from django.http.response import Http404
from dry_rest_permissions.generics import DRYPermissions
from rest_framework.generics import ListAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.serializers import ModelSerializer
from rest_framework import filters
from rest_framework_extensions.etag.decorators import etag
from rest_framework_extensions.cache.decorators import cache_response
from zds.member.api.permissions import CanReadAndWriteNowOrReadOnly, IsNotOwnerOrReadOnly
from zds.member.api.views import PagingSearchListKeyConstructor
from zds.utils import get_current_user
from zds.utils.api.views import KarmaView
from zds.tutorialv2.models.models_database import ContentReaction, VerbVote, Verb, PublishableContent


class ContentReactionKarmaView(KarmaView):
    queryset = ContentReaction.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly, CanReadAndWriteNowOrReadOnly, IsNotOwnerOrReadOnly)


class VerbCastSerializer(ModelSerializer):
    class Meta:
        model = VerbVote
        fields = ('verb', 'content__title')
        permissions_classes = DRYPermissions


class ContentCast(CreateAPIView):
    permission_classes = (IsAuthenticated, )  # TODO : ban banned user
    list_key_func = PagingSearchListKeyConstructor()
    serializer_class = VerbCastSerializer

    def post(self, request, *args, **kwargs):
        try:
            verb = Verb.objects.filter(label=request.POST.get("verb")).first()
            if verb is None:
                raise Http404("No such verb")
            content = PublishableContent.objects.filter(content__pk=request.POST.get("content")).first()
            if content is None:
                raise Http404("No such content")
            vote = VerbVote(caster=get_current_user(), verb=verb, content=content)
            vote.save()

        except KeyError as e:
            self.response.status_code = 400
            self.response.write(str(e))
