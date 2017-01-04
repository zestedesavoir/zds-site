# -*- coding: utf-8 -*-

from rest_framework import permissions
from django.contrib.auth.models import AnonymousUser
from zds.forum.models import Forum



class IsStaffUser(permissions.BasePermission):
    """
    Allows access only to staff users.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_staff


class IsOwnerOrIsStaff(permissions.BasePermission):
    """
    Allows access only to staff users or object owner.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the snippet
        if hasattr(obj, 'user'):
            author = obj.user
        elif hasattr(obj, 'author'):
            author = obj.author
        else:
            author = AnonymousUser()
        
        print(request.user)
        print(author)
        print(request.user.has_perm("forum.change_topic"))
        return (author == request.user) or (request.user.has_perm("forum.change_topic")) 

class CanWriteInForum(permissions.BasePermission):
    """
    Allows access only to people that can write in this forum.
    """

    def has_permission(self, request, view):
        print('can write forum')
        print(request.data)
        forum = Forum.objects.get(id=request.data.get('forum')) # TODO tester si on met un id qui n'existe pas
        return forum.can_read(request.user)
        
class CanWriteInTopic(permissions.BasePermission):
    """
    Allows access only to people that can write in this topic.
    """

    def has_permission(self, request, view):
        print('can write topic')
        #print(request.data)
        #topic = Forum.objects.get(id=request.data.get('forum')) # TODO tester si on met un id qui n'existe pas
        #forum.can_read(request.user)    
        return True