from functools import lru_cache

from django import template
from django.contrib.auth.models import User
from django.core.cache import cache

from zds.member.models import Profile

register = template.Library()


@register.filter("profile")
@lru_cache
def profile(current_user):
    # we currently expect to receive a User in most cases, but as we move
    # toward using Profiles instead, we have to handle them as well.
    try:
        return current_user.profile
    except AttributeError:
        if isinstance(current_user, Profile):
            return current_user
    except Profile.DoesNotExist:
        pass
    return None


@register.filter("user")
def user(user_pk):
    try:
        current_user = User.objects.get(pk=user_pk)
    except User.DoesNotExist:
        current_user = None
    return current_user


@register.filter(name="groups")
def user_groups(user):
    if user.pk is None:
        user_identifier = "unauthenticated"
    else:
        user_identifier = user.pk

    key = f"user_pk={user_identifier}_groups"
    groups = cache.get(key)

    if groups is None:
        try:
            current_user_groups = (
                User.objects.filter(pk=user.pk).prefetch_related("groups").values_list("groups", flat=True)
            )
        except User.DoesNotExist:
            current_user_groups = ["none"]
        groups = "{}-{}".format("groups", "-".join(str(current_user_groups)))
        cache.set(key, groups, 4 * 60 * 60)
    return groups


@register.filter("state")
def state(current_user):
    try:
        user_profile = current_user.profile
        if not user_profile.user.is_active:
            user_state = "DOWN"
        elif not user_profile.can_read_now():
            user_state = "BAN"
        elif not user_profile.can_write_now():
            user_state = "LS"
        else:
            user_state = None
    except Profile.DoesNotExist:
        user_state = None
    return user_state


@register.inclusion_tag("misc/avatar.part.html")
def avatar(profile: Profile, size=80) -> dict:
    if profile is not None:
        return {
            "avatar_url": profile.avatar_url,
            "avatar_size": size,
            "username": profile.user.username,
        }
