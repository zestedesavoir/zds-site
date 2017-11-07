import contextlib
from pathlib import Path

from django.http import Http404
from django.utils import translation
from django.utils.translation import gettext as _
from rest_framework import status
from rest_framework.fields import empty
from rest_framework.generics import UpdateAPIView, ListCreateAPIView, get_object_or_404
from rest_framework.response import Response
from rest_framework.serializers import Serializer, CharField, BooleanField
from rest_framework.generics import RetrieveUpdateAPIView, ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.exceptions import ValidationError

from zds.tutorialv2.publication_utils import PublicatorRegistry
from zds.member.api.permissions import IsAuthorOrStaff
from zds.member.api.permissions import CanReadAndWriteNowOrReadOnly, IsNotOwnerOrReadOnly
from zds.tutorialv2.api.permissions import IsOwner, CanModerate
from zds.tutorialv2.api.serializers import ChildrenListSerializer, ChildrenListModifySerializer, \
    PublishableMetaDataSerializer
from zds.tutorialv2.api.view_models import ChildrenListViewModel, ChildrenViewModel
from zds.tutorialv2.mixins import SingleContentDetailViewMixin
from zds.tutorialv2.models.versioned import Extract, Container
from zds.tutorialv2.utils import search_container_or_404
from zds.utils.api.views import KarmaView
from zds.tutorialv2.models.database import ContentReaction, PublishableContent, PublicationEvent


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


class ExportView(ListCreateAPIView):
    permission_classes = (IsAuthorOrStaff,)
    serializer_class = Serializer

    def get_queryset(self):
        return PublicationEvent.objects.filter(published_object__content__pk=self.kwargs.get('pk', 0))

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


class RedactionChildrenListView(SingleContentDetailViewMixin, RetrieveUpdateAPIView):
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        versioned_object = self.get_versioned_object()
        parent = search_container_or_404(versioned_object, kwargs)
        list_model = ChildrenListViewModel()
        if parent.has_extracts():
            children = [ChildrenViewModel('extract', e.title, None, e.get_text(), e.slug) for e in parent.children]
            list_model.extracts += children
        if parent.has_sub_containers():
            children = [ChildrenViewModel('container', e.title, e.description, e.text, e.slug) for e in parent.children]
            list_model.containers += children
        list_model.conclusion = parent.get_conclusion()
        list_model.introduction = parent.get_introduction()
        serializer = self.get_serializer(list_model)
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        """
        Modify part or chapter
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        self.object = self.get_object()
        versioned_object = self.get_versioned_object()
        self.parent = search_container_or_404(versioned_object, kwargs)
        existing_slugs = [child.slug for child in self.parent.children]
        serializer = self.get_serializer_class()(data=request.data, context={'request': request}, db_object=self.object)
        serializer.is_valid(raise_exception=True)
        view_model = serializer.create(serializer.validated_data)
        sent_slug = [child.slug for child in view_model.get_used_children()]
        searched_children = 'container'
        if self.parent.has_extracts() or not self.parent.can_add_container() or self.parent.can_add_extract():
            searched_children = 'extract'
        if not view_model.get_used_children()[0].child_type == searched_children:
            raise ValidationError('bad type')
        removed_slugs = list(set(existing_slugs) - set(sent_slug))
        if removed_slugs and view_model.remove_deleted_children:
            for slug in removed_slugs:
                self.parent.children_dict[slug].repo_delete(do_commit=False)
        for i, child_view_model in enumerate(view_model.get_used_children()):
            self.add_child_to_parent(child_view_model, i, Extract if searched_children == 'extract' else Container)
        sha = self.parent.repo_update(self.parent.title, view_model.introduction, view_model.conclusion,
                                      view_model.commit_message or 'mise à jour', update_slug=False, do_commit=True)
        self.object.sha_draft = sha
        self.object.save()
        return Response({'result': 'OK', 'sha': sha}, content_type='application/json')

    def patch(self, request, *args, **kwargs):
        return self.put(request, *args, **kwargs)

    def add_child_to_parent(self, child_view_model, position, type_class):
        stored = type_class(slug=child_view_model.slug, title=child_view_model.title,
                            position_in_parent=position, container=self.parent)
        if child_view_model.slug not in self.parent.children_dict:
            self.parent.add_extract(stored, False)
        else:
            stored = self.parent.children_dict[stored.slug]
        index = self.parent.children.index(stored)
        while index != position:  # handle insertion and moving
            self.parent.children[index], self.parent.children[index - 1] = \
                self.parent.children[index - 1], self.parent.children[index]
            index -= 1
        if child_view_model.child_type.lower() == 'extract':
            stored.repo_update(stored.title, child_view_model.text, do_commit=False)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ChildrenListSerializer
        elif self.request.method == 'PUT':
            return ChildrenListModifySerializer
        return ChildrenListSerializer

    def get_permissions(self):
        return [IsAuthenticatedOrReadOnly()]


class AuthorContentListCreateAPIView(ListCreateAPIView):
    permission_classes = (IsOwner, CanModerate)
    serializer_class = PublishableMetaDataSerializer

    def get_queryset(self):
        return PublishableContent.objects.filter(authors__pk__in=[self.kwargs.get('user')])


class InRedactionContentRetrieveUpdateDeleteAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = (IsOwner, CanModerate)
    serializer_class = PublishableMetaDataSerializer

    def get_object(self):
        return get_object_or_404(PublishableContent, pk=self.kwargs.get('pk'))
