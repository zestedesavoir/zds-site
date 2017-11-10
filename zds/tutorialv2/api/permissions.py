from rest_framework.permissions import BasePermission, DjangoModelPermissions


class IsOwner(BasePermission):
    owner_mark = 'author'

    @staticmethod
    def is_owner(request):

        request_param_user = request.parser_context['kwargs'].get('user', '0')
        current_user = request.user
        try:
            return current_user and current_user.pk == int(request_param_user)
        except ValueError:  # not an int
            return False

    def is_object_owner(self, request, object):
        request_param_user = request.parser_context['kwargs'].get('user', 0)
        try:
            object_owner = getattr(object, self.owner_mark, None).pk
            return request_param_user == object_owner
        except AttributeError:
            return False

    def has_permission(self, request, view):
        return IsOwner.is_owner(request)

    def has_object_permission(self, request, view, obj):
        return self.is_object_owner(request, obj)


class CanModerate(DjangoModelPermissions):
    perms_map = {
        'GET': ['%(app_label)s.change_%(model_name)s'],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }


class CanModerateOrIsOwner(CanModerate, IsOwner):
    def has_permission(self, request, view):
        return IsOwner.is_owner(request) or CanModerate.has_permission(self, request, view)
