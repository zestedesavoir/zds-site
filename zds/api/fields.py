# coding: utf-8

from rest_framework import serializers

class UnixDateField(serializers.DateTimeField):
    """
    Field to convert a Django datetime field to a Unix field.
    """
    def to_native(self, value):
        """
        Returns timestamp for a datetime object or None.
        """
        import time
        try:
            return int(time.mktime(value.timetuple()))
        except (AttributeError, TypeError):
            return None

    def from_native(self, value):
        """
        Returns a datetime object for a timestamp.
        """
        import datetime
        return datetime.datetime.fromtimestamp(int(value))

class HtmlField(serializers.Field):
    def to_native(self, value):
        """
        Returns html path of the tutorial given.
        """
        try:
            return '/tutoriels/telecharger/html/?tutoriel={0}'.format(int(value))
        except TypeError:
            return None

class ArticleArchiveLinkField(serializers.Field):
    """
    Field to format hyperlink to retreive hyperlink of an article's archive.
    """
    def to_native(self, value):
        """
        Returns html path of the article given.
        """
        try:
            return '/articles/telecharger/?article={0}'.format(int(value))
        except TypeError:
            return None