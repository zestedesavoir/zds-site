from __future__ import unicode_literals
from django.utils.text import slugify
from rest_framework.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _


class ChildrenViewModel(object):
    class Meta:
        pass

    def __init__(self, child_type, title, description=None, text=None, slug=None):
        self.child_type = child_type
        self.title = title
        if child_type == 'extract' and description:
            raise ValidationError({'extracts': _('Un extrait ne peut avoir de description')})
        self.description = description
        self.slug = slugify(slug) or slugify(title)
        if not slug or slug in ['introduction', 'conclusion']:
            raise ValidationError({'exctracts': _('Un extrait doit avoir un titre complet qui ne soit ni Introduction,'
                                                  ' ni Conclusion')})
        if child_type == 'container' and text:
            raise ValidationError({'containers': 'Une partie ou un chapitre ne peut contenir de texte.'})
        self.text = text

    def has_write_permission(self):
        return True


class ChildrenListViewModel(object):
    class Meta:
        pass

    def __init__(self, extracts=None, containers=None, introduction=None, conclusion=None, authors=None,
                 original_sha='', **__):
        self.extracts = extracts or []
        self.containers = containers or []
        self.introduction = introduction or ''
        self.conclusion = conclusion or ''
        self.authors = authors or []
        self.original_sha = original_sha

    def get_used_children(self):
        if self.extracts:
            return self.extracts[:]
        else:
            return self.containers[:]

    @staticmethod
    def has_read_permission(request):
        return True

    @staticmethod
    def has_write_permission(request):
        return False

    def has_object_read_permission(self, request):
        return request.user.is_authenticated() and request.user in self.db


class UpdateChildrenListViewModel(ChildrenListViewModel):
    remove_deleted_children = False
    message = None

    class Meta:
        pass

    def __init__(self, extracts=None, containers=None, introduction=None, conclusion=None, authors=None,
                 remove_deleted_children=False, message='', **__):
        super(UpdateChildrenListViewModel, self).__init__(extracts, containers, introduction, conclusion, authors)
        self.remove_deleted_children = remove_deleted_children
        self.message = message

    @property
    def commit_message(self):
        return self.message or ''

    @staticmethod
    def has_write_permission(request):
        return True
