# coding: utf-8
import json
import logging

from django.db.models.aggregates import Count
from django.http.response import Http404
from dry_rest_permissions.generics import DRYPermissions
from rest_framework.generics import ListAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.serializers import ModelSerializer
from rest_framework.serializers import Serializer
from rest_framework.response import Response

from zds.member.api.permissions import CanReadAndWriteNowOrReadOnly, IsNotOwnerOrReadOnly
from zds.member.api.views import PagingSearchListKeyConstructor
from zds.utils import get_current_user
from zds.utils.api.views import KarmaView
from zds.tutorialv2.models.models_database import ContentReaction, VerbVote, Verb, PublishableContent
from django.template.loader import render_to_string


class ContentReactionKarmaView(KarmaView):
    queryset = ContentReaction.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly, CanReadAndWriteNowOrReadOnly, IsNotOwnerOrReadOnly)


class VerbCastSerializer(ModelSerializer):
    class Meta:
        model = VerbVote
        fields = ('verb', 'content')
        permissions_classes = DRYPermissions


class ContentCast(CreateAPIView):
    permission_classes = (IsAuthenticated, )  # TODO : ban banned user
    serializer_class = VerbCastSerializer

    def post(self, request, *args, **kwargs):
        try:
            post = json.loads(request.body)
            print(post)
            verb = Verb.objects.filter(label=post.get("verb")).first()
            logging.warn("%s cast", verb)
            if verb is None:
                raise Http404("No such verb")
            content = PublishableContent.objects.filter(pk=int(post.get("content__pk"))).first()
            logging.warn("%s cast", content)
            if content is None:
                raise Http404("No such content")
            vote = VerbVote(caster=get_current_user(), verb=verb, content=content)
            vote.save()

        except (KeyError, ValueError) as e:
            self.response.status_code = 400
            self.response.write(str(e))
            logging.warn("error %s", e)
        return Response({"result": "ok"})


class ContentSerializer(ModelSerializer):
    class Meta:
        model = PublishableContent
        fields = ("title", "authors", "description", "image", "tags", "subcategory")
        permission_classes = DRYPermissions


class VerbSerializer(ModelSerializer):
    class Meta:
        model = Verb
        fields = ("label", "sentence_label")
        permission_classes = DRYPermissions


class VerbListFilteringView(ListAPIView):
    category = None
    serializer_class = VerbSerializer

    def get_queryset(self):
        if self.category:
            return VerbVote.objects.get_verb_for_category(self.category)
        return Verb.objects.all()

    def get(self, request, *args, **kwargs):
        self.category = request.GET.get("category", None)
        return super(VerbListFilteringView, self).get(request, *args, **kwargs)


class ContentListFilteringView(ListAPIView):  # just learn to use DRF and go back generic use of it
    """
    filter content by category, subcategory, tag and verb
    """
    # no auth is needed
    verb = None
    category = None
    tags = []

    def get_queryset(self):
        """
        TODO: please get it faster.
        :return: the publishablecontent list
        :rtype: iterable[PublishableContent]
        """
        filters = {}

        if self.category:
            prop_filter = lambda c: len([cat.category.title for cat in c.subcategory.all() if cat.category.title == self.category]) > 0
        else:
            prop_filter = None
        if self.tags:
            filters["tags__slug__in"] = self.tags
        if self.verb:
            filters["pk__in"] = VerbVote.objects.filter(verb__label=self.verb)\
                .annotate(nb_vote=Count("verb__label"))\
                .order_by('nb_vote')\
                .values_list("content__pk", flat=True)
        print(filters)
        # i'm forced to use a python filter as subcategory__catecory is a property, not a field
        filtered = filter(prop_filter, PublishableContent.objects.prefetch_related("tags").filter(**filters))
        return filtered[:10]

    def get(self, request, *args, **kwargs):
        self.verb = request.GET.get("verb", None)
        self.tags = request.GET.get("tags", "").split(",")
        if self.tags[0] == "":
            self.tags = []
        self.category = request.GET.get("category", None)
        if not any([self.verb, self.tags, self.category]):
            raise Http404("Pas de bras, pas de chocolat.")
        query_set = self.get_queryset()
        data = [self._render_content(c) for c in query_set]
        tags = set()
        map(lambda c: tags.update(list(c.tags.all())), query_set)
        return Response({"results": data, "tags": [t.title for t in tags]})

    def _render_content(self, content):
        return render_to_string("tutorialv2/includes/content_item.part.html", {"public_content": content.public_version})
