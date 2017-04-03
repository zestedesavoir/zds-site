from zds.forum.models import Forum


def get_authorized_forums(user):
    """
    Find forums the user is allowed to visit.

    :param user: concerned user.
    :return: authorized_forums
    """
    forums_pub = Forum.objects.filter(groups__isnull=True).all()
    if user and user.is_authenticated():
        forums_private = Forum \
            .objects \
            .filter(groups__isnull=False, groups__in=user.groups.all()) \
            .all()
        list_forums = list(forums_pub | forums_private)
    else:
        list_forums = list(forums_pub)

    return [f.pk for f in list_forums]
