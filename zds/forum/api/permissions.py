# -*- coding: utf-8 -*-

from rest_framework import permissions
from django.contrib.auth.models import AnonymousUser
from zds.forum.models import Forum, Topic, Post
from django.http import Http404
from django.shortcuts import get_object_or_404


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

        return (author == request.user) or (request.user.has_perm('forum.change_topic'))


class CanWriteInForum(permissions.BasePermission):
    """
    Allows access only to people that can write in forum passed by post request.
    """

    def has_permission(self, request, view):
        forum = get_object_or_404(Forum, id=request.data.get('forum'))
        return forum.can_read(request.user)


class CanWriteInTopic(permissions.BasePermission):
    """
    Allows access only to people that can write in topic passed by url.
    """

    def has_permission(self, request, view):

        topic_pk = request.resolver_match.kwargs.get('pk')
        topic = get_object_or_404(Topic, id=topic_pk)

        # Antispam function returns true when user CAN'T post.
        if topic.antispam(request.user):
            return False
        else:
            return (topic.forum.can_read(request.user)) and (not topic.is_locked or request.user.has_perm('forum.change_post'))


class CanAlertPost(permissions.BasePermission):
    """
    Allows access only to people that can write in topic passed by url. TODO
    """

    def has_permission(self, request, view):

        topic_pk = request.resolver_match.kwargs.get('pk_sujet')
        topic = get_object_or_404(Topic, id=topic_pk)

        # Fonctionner avec obj. ?  TODO
        return topic.forum.can_read(request.user)


class CanEditPost(permissions.BasePermission):
    """
    Allows access only to people that can edit the topic.
    """

    def has_permission(self, request, view):
        topic_pk = request.resolver_match.kwargs.get('pk_sujet')
        topic = get_object_or_404(Topic, id=topic_pk)
        post_pk = request.resolver_match.kwargs.get('pk')
        post = get_object_or_404(Post, id=post_pk)

        # Can edit topic if user is admin
        # Or topic is not locked and user is topic owner
        return request.user.has_perm('forum.change_post') or (not topic.is_locked and post.author == request.user)
