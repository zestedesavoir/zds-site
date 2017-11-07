from rest_framework.permissions import BasePermission, DjangoModelPermissions


class IsOwner(BasePermission):
    def has_permission(self, request, view):
        request_param_user = request.kwargs.get('user', 0)
        current_user = request.user
        return current_user and current_user.pk == request_param_user


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
