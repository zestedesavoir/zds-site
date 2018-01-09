from django.http import Http404
from django.utils.translation import gettext as _
from rest_framework.fields import empty
from rest_framework.generics import UpdateAPIView
from rest_framework.serializers import Serializer, CharField, BooleanField
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from zds.member.api.permissions import CanReadAndWriteNowOrReadOnly, IsNotOwnerOrReadOnly, IsStaffUser, IsOwner
from zds.tutorialv2.utils import search_container_or_404
from zds.utils.api.views import KarmaView
from zds.tutorialv2.models.database import ContentReaction, PublishableContent


class ContainerReadinessSerializer(Serializer):
    parent_container_slug = CharField()
    container_slug = CharField(required=True)
    ready_to_publish = BooleanField(required=True)

    def run_validation(self, data=empty):
        init = super().run_validation(data)
        if not init:
            return init
        if not data.get('parent_container_slug', ''):
            init.pop('parent_container_slug', '')
        return init

    def save(self, **kwargs):
        if not self.validated_data:
            self.is_valid(True)
        versioned = self.instance.load_version()
        container = search_container_or_404(versioned, self.validated_data)
        container.ready_to_publish = self.validated_data['ready_to_publish']
        sha = versioned.repo_update(versioned.title, versioned.get_introduction(), versioned.get_conclusion(),
                                    commit_message=_('{} est {} à la publication.').format(
                                        container.get_path(True),
                                        _('prêt') if container.ready_to_publish else _('ignoré')))
        PublishableContent.objects.filter(pk=self.instance.pk).update(sha_draft=sha)

    def to_representation(self, instance):
        return {}


class ContentReactionKarmaView(KarmaView):
    queryset = ContentReaction.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly, CanReadAndWriteNowOrReadOnly, IsNotOwnerOrReadOnly)


class ContainerPublicationReadinessView(UpdateAPIView):
    permission_classes = (IsStaffUser, IsOwner)
    serializer_class = ContainerReadinessSerializer

    def get_object(self):
        content = PublishableContent.objects.prefetch_related('authors')\
            .filter(pk=int(self.kwargs['pk']))\
            .first()
        if not content:
            raise Http404()
        return content
