# -*- coding: utf-8 -*-

from rest_framework import permissions
from django.contrib.auth.models import AnonymousUser
from zds.forum.models import Forum, Topic, Post
from django.http import Http404


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

        return (author == request.user) or (request.user.has_perm("forum.change_topic"))


class CanWriteInForum(permissions.BasePermission):
    """
    Allows access only to people that can write in forum passed by post request.
    """

    def has_permission(self, request, view):

        try:
            forum = Forum.objects.get(id=request.data.get('forum'))
        except Forum.DoesNotExist:
            raise Http404("Forum with pk {} was not found".format(request.data.get('forum')))

        return forum.can_read(request.user)


class CanWriteInTopic(permissions.BasePermission):
    """
    Allows access only to people that can write in topic passed by url.
    """

    def has_permission(self, request, view):

        topic_pk = request.resolver_match.kwargs.get('pk')
        try:
            topic = Topic.objects.get(id=topic_pk)
        except Topic.DoesNotExist:
            print('pas trouve')
            raise Http404("Topic with pk {} was not found".format(topic_pk))
        # Fonctionner avec obj. ?  TODO
        # Antispam function returns true when user CAN'T post.
        if topic.antispam(request.user):
            print('antispam refuse')
            return False
        else:
            return (topic.forum.can_read(request.user)) and (not topic.is_locked or request.user.has_perm("forum.change_post"))
            
            
class CanAlertPost(permissions.BasePermission):
    """
    Allows access only to people that can write in topic passed by url. TODO 
    """

    def has_permission(self, request, view):

        topic_pk = request.resolver_match.kwargs.get('pk_sujet')
        try:
            topic = Topic.objects.get(id=topic_pk)
        except Topic.DoesNotExist:
            raise Http404("Topic with pk {} was not found".format(topic_pk))
            
        # Fonctionner avec obj. ?  TODO
        print('can alert post')
        print(topic.forum.can_read(request.user))
        return topic.forum.can_read(request.user)


class CanEditPost(permissions.BasePermission):
    """
    Allows access only to people that can edit the topic.
    """

    def has_permission(self, request, view):
        topic_pk = request.resolver_match.kwargs.get('pk_sujet')
        print('can edit post')

        try:
            topic = Topic.objects.get(id=topic_pk)
        except Topic.DoesNotExist:
            print('can edit post : topic non trouve')
            raise Http404("Topic with pk {} was not found".format(topic_pk))

        post_pk = request.resolver_match.kwargs.get('pk')

        try:
            post = Post.objects.get(id=post_pk)
        except Post.DoesNotExist:
            print('can edit post : post non trouve')
            raise Http404("Post with pk {} was not found".format(post_pk))

        # Can edit topic if user is admin
        # Or topic is not locked and user is topic owner
        print('fin can edit post')
        return request.user.has_perm("forum.change_post") or (not topic.is_locked and post.author == request.user)
        
        # TODO utiliser partout get_object_or_404 ?