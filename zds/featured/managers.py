from datetime import datetime

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from zds.forum.models import Topic
from zds.utils import get_current_user


class FeaturedResourceManager(models.Manager):
    """
    Custom featured resource manager.
    """

    def get_last_featured(self):
        return (
            self.order_by("-pubdate")
            .exclude(pubdate__gt=datetime.now())
            .prefetch_related("authors__user")[: settings.ZDS_APP["featured_resource"]["home_number"]]
        )


class FeaturedMessageManager(models.Manager):
    """
    Custom featured message manager.
    """

    def get_last_message(self):
        return self.last()


class FeaturedRequestedException(Exception):
    pass


class FeaturedRequestedManager(models.Manager):
    """Custom manager"""

    def get_existing(self, content_object):
        """Get existing object for ``content_object``

        :param content_object: object on which the request is done
        :type content_object: zds.forum.models.Topic|zds.tutorialv2.models.database.PublishableContent
        :rtype: zds.featured.models.FeaturedRequested|None
        """
        content_type = ContentType.objects.get_for_model(content_object)

        try:
            featured_request = (
                self.filter(object_id=content_object.pk, content_type__pk=content_type.pk)
                .prefetch_related("users_voted")
                .last()
            )
        except ObjectDoesNotExist:
            featured_request = None

        return featured_request

    def get_or_create(self, content_object):
        """Get or create object for ``content_object``

        :param content_object: object on which the request is done
        :type content_object: zds.forum.models.Topic|zds.tutorialv2.models.database.PublishableContent
        :rtype: zds.featured.models.FeaturedRequested
        """
        featured_request = self.get_existing(content_object)
        if featured_request is None:
            featured_request = self.model(
                content_object=content_object, type="TOPIC" if isinstance(content_object, Topic) else "CONTENT"
            )
            featured_request.save()

        return featured_request

    def requested_and_count(self, content_object, user):
        """Count number of vote on ``content_object``

        :param content_object: object on which the request is done
        :type content_object: zds.forum.models.Topic|zds.tutorialv2.models.database.PublishableContent
        :param user: the user
        :type user: User
        :return: tuple of the form (show, user has voted, number of votes)
        :rtype: (bool, bool, int)
        """
        featured_request = self.get_existing(content_object)

        if featured_request is None:
            return True, False, 0
        else:
            users = list(u for u in featured_request.users_voted.all())
            return not featured_request.rejected_for_good, user in users, len(users)

    def toogle_request(self, content_object, user=None):
        """Toogle featured request for user on ``content_object`

        :param content_object: object on which the request is done
        :type content_object: zds.forum.models.Topic|zds.tutorialv2.models.database.PublishableContent
        :param user: the user
        :type user: User
        :return: tuple of the form (user has voted, number of votes)
        :rtype: (bool, int)
        """

        if user is None:
            user = get_current_user()
        if user is None:
            raise FeaturedRequestedException("cannot toggle without connected user")

        featured_request = self.get_or_create(content_object)
        if featured_request.rejected_for_good:
            raise FeaturedRequestedException("cannot toogle request rejected for good!")

        return featured_request.toggle(user)
