from rest_framework.exceptions import ValidationError
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from zds.member.api.permissions import CanReadAndWriteNowOrReadOnly, IsNotOwnerOrReadOnly
from zds.tutorialv2.api.serializers import ChildrenListSerializer, ChildrenListModifySerializer
from zds.tutorialv2.api.view_models import ChildrenListViewModel, ChildrenViewModel
from zds.tutorialv2.mixins import SingleContentDetailViewMixin
from zds.tutorialv2.models.models_versioned import Extract, Container
from zds.tutorialv2.utils import search_container_or_404
from zds.utils.api.views import KarmaView
from zds.tutorialv2.models.database import ContentReaction


class ContentReactionKarmaView(KarmaView):
    queryset = ContentReaction.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly, CanReadAndWriteNowOrReadOnly, IsNotOwnerOrReadOnly)


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
