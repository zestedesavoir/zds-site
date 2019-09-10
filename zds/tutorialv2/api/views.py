import contextlib
from pathlib import Path

from django.http import Http404
from django.utils import translation
from django.utils.translation import gettext as _
from rest_framework import status
from rest_framework.fields import empty
from rest_framework.generics import UpdateAPIView, CreateAPIView, get_object_or_404
from rest_framework.response import Response
from rest_framework.serializers import Serializer, CharField, BooleanField
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from zds.member.api.permissions import CanReadAndWriteNowOrReadOnly, IsNotOwnerOrReadOnly, IsAuthorOrStaff
from zds.tutorialv2.publication_utils import PublicatorRegistry
from zds.tutorialv2.utils import search_container_or_404
from zds.utils.api.views import KarmaView
from zds.tutorialv2.models.database import ContentReaction, PublishableContent


class ContainerReadinessSerializer(Serializer):
    parent_container_slug = CharField(allow_blank=True, allow_null=True, required=False)
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
    permission_classes = (IsAuthorOrStaff, )
    serializer_class = ContainerReadinessSerializer

    def get_object(self):
        content = PublishableContent.objects.prefetch_related('authors')\
            .filter(pk=int(self.kwargs.get('pk', 0)))\
            .first()
        if not content:
            raise Http404()
        self.check_object_permissions(self.request, object)
        return content


class ExportView(CreateAPIView):
    permission_classes = (IsAuthorOrStaff,)
    serializer_class = Serializer

    def ensure_directories(self, content: PublishableContent):
        final_directory = Path(content.public_version.get_extra_contents_directory())
        building_directory = Path(str(final_directory.parent) + '__building', final_directory.name)
        with contextlib.suppress(FileExistsError):
            final_directory.mkdir(parents=True)
        with contextlib.suppress(FileExistsError):
            building_directory.mkdir(parents=True)
        return building_directory, final_directory

    def create(self, request, *args, **kwargs):
        try:
            publishable_content = get_object_or_404(PublishableContent.objects, pk=int(kwargs.get('pk')))
            if not publishable_content.public_version:
                raise Http404('Not public content')
            tmp_dir, _ = self.ensure_directories(publishable_content)
            versioned = publishable_content.public_version.load_public_version()
            base_name = str(Path(tmp_dir, versioned.slug))
            md_file_path = str(Path(tmp_dir, versioned.slug + '.md'))

            PublicatorRegistry.get('md').publish(md_file_path, base_name,
                                                 versioned=versioned,
                                                 cur_language=translation.get_language())
            PublicatorRegistry.get('watchdog').publish_from_published_content(publishable_content.public_version)
        except ValueError:
            return Response({}, status=status.HTTP_400_BAD_REQUEST, headers={})
        else:
            return Response({}, status=status.HTTP_201_CREATED, headers={})
