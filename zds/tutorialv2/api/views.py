# coding: utf-8
from django.db.models.aggregates import Count
from django.http.response import Http404
from dry_rest_permissions.generics import DRYPermissions
from rest_framework.generics import ListAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.serializers import ModelSerializer
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


class ContentSerializer(ModelSerializer):
    class Meta:
        model = PublishableContent
        fields = ("title", "authors", "description", "image", "tags", "subcategory")
        permission_classes = DRYPermissions


class VerbListFilteringView(ListAPIView):
    category = None

    def get_queryset(self):
        if self.category:
            return VerbVote.objects.get_verb_label_for_category()
        return Verb.objects.values_list("label", flat=True)

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
            filters["content__subcategory__category__label"] = self.category
        if self.tags:
            filters["content__tags__slug__in"] = self.tags
        if self.verb:
            filters["pk__in"] = VerbVote.objects.filter(verb__label=self.verb)\
                .prefetch_related("content")\
                .aggregate(nb_vote=Count("verb__label"))\
                .order_by('nb_vote')\
                .values_list("content__pk", flat=True)
        return PublishableContent.objects.filter(**filters)[:10]

    def get(self, request, *args, **kwargs):
        self.verb = request.GET.get("verb", None)
        self.tags = request.GET.get("tags", "").split(",")
        self.category = request.GET.get("category", None)
        if not any(self.verb, self.tags, self.category):
            raise Http404("Pas de bras, pas de chocolat.")
        query_set = self.get_queryset()
        data = [self._render_content(c) for c in query_set]
        return Response(data)

    def _render_content(self, content):
        render_to_string("tutorialv2/includes/content_item.part.html", {"public_content": content})
