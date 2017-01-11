import logging
from collections import Counter

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from zds.tutorialv2.api.view_models import ChildrenViewModel, ChildrenListViewModel, UpdateChildrenListViewModel
from gettext import gettext as _

logger = logging.getLogger(__name__)


def transform(exception1, exception2, message):
    """
    Decorates a method so that it can wrap some error into a more convenient type

    :param exception1: former exception class
    :type exception1: Type
    :param exception2: raised exception class
    :type exception2: Type
    :param message: the message to send to newly raised exception
    :raises: exception2
    """
    def wrapper(func):
        def decorated(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exception1:
                logger.warning('Error translated fril %s to %s', exception1, exception2(message))
                raise exception2(message)
        return decorated
    return wrapper


class ChildrenSerializer(serializers.Serializer):
    text = serializers.CharField(source='text', allow_blank=True, allow_null=False, required=False, default='')

    class Meta:
        model = ChildrenViewModel
        fields = ('child_type', 'title', 'description', 'text')


class ChildrenListSerializer(serializers.Serializer):
    """
    Serialize children list so that api can handle them
    """

    def update(self, instance, validated_data):
        pass

    extracts = serializers.ListField(child=ChildrenSerializer(), source='extracts')
    containers = serializers.ListField(child=ChildrenSerializer(), source='containers')
    extract_number = serializers.IntegerField(source='extracts.__len__')
    container_number = serializers.IntegerField(source='containers.__len__')
    introduction = serializers.CharField(source='introduction', required=False, default='', allow_null=False)
    conclusion = serializers.CharField(source='conclusion', required=False, default='', allow_null=False)

    class Meta:
        fields = ('extracts', 'containers', 'extract_number', 'container_number',
                  'introduction', 'conclusion')

    def __init__(self, *args, **kwargs):
        self.db_object = kwargs.pop('db_object', None)
        super(ChildrenListSerializer, self).__init__(*args, **kwargs)
        self._validated_data = {}
        self._errors = {}

    def create(self, validated_data):
        return ChildrenListViewModel(**validated_data)

    def save(self, **kwargs):
        self.is_valid(True)
        return self.create(self.validated_data)

    @transform(TypeError, ValidationError, 'incorrect json')
    def is_valid(self, raise_exception=False):
        """
        This method overrides ``ModelSerializer`` method. If someone knows a cleaner way, dig it.

        :param raise_exception:
        :return:
        """

        error = not super(ChildrenListSerializer, self).is_valid(raise_exception)
        messages = {}

        for field_name, value in self.initial_data.items():
            if field_name in self.Meta.fields:
                self._validated_data[field_name] = value
        if self._validated_data.get('extracts', None):
            self._validated_data['extracts'] = [ChildrenViewModel(**v) for v in self._validated_data['extracts']]
        if self.initial_data.get('containers', None):
            self._validated_data['containers'] = [ChildrenViewModel(**v) for v in self._validated_data['containers']]
        if not all(c.child_type.lower() == 'extract' for c in self._validated_data.get('extracts', [])):
            error = True
            messages['extracts'] = _('un extrait est mal configuré')
        if len(self._validated_data['extracts']) != len(set(e.title for e in self._validated_data['extracts'])):
            error = True
            titles = Counter(list(e.title for e in self._validated_data['extracts']))
            doubly = [key for key, v in titles.items() if v > 1]
            messages['extracts'] = _('Certains titres sont en double : {}').format(','.join(doubly))
        if len(self._validated_data['containers']) != len(set(e.title for e in self._validated_data['containers'])):
            error = True
            titles = Counter(list(e.title for e in self._validated_data['containers']))
            doubly = [key for key, v in titles.items() if v > 1]
            messages['containers'] = _('Certaines parties ou chapitres sont en double : {}').format(','.join(doubly))
        if not all(c.child_type.lower() == 'container' for c in self._validated_data.get('containers', [])):
            error = True
            messages['containers'] = _('Un conteneur est mal configuré')
        self._validated_data['introduction'] = self.initial_data.get('introduction', '')
        self._validated_data['conclusion'] = self.initial_data.get('conclusion', '')
        if not self._validated_data['extracts'] and not self._validated_data['containers']:
            error = True
            messages['extracts'] = _('Le contenu semble vide.')
        if raise_exception and error:
            self._errors.update(messages)
            raise ValidationError(self.errors)

        return not error

    def to_representation(self, instance):
        dic_repr = {}
        for key in instance.__dict__:
            if not key.startswith('_') and not callable(getattr(instance, key)):
                dic_repr[key] = getattr(instance, key)
            elif not key.startswith('_') and hasattr(self, key):
                dic_repr = getattr(self, key).get_value()
            if isinstance(dic_repr[key], list):
                dic_repr[key] = [self.to_representation(i) for i in dic_repr[key]]

        return dic_repr


class ChildrenListModifySerializer(ChildrenListSerializer):
    """
    add the `remove_deleted_children` to the base serializer so that we can tell the api we want to delete every \
    element that exist in git repo but not in the request
    """
    remove_deleted_children = serializers.BooleanField(source='remove_deleted_children')
    message = serializers.CharField(source='message', required=False)
    original_sha = serializers.CharField(source='original_sha', required=False, default='', allow_null=False)

    class Meta:
        model = UpdateChildrenListViewModel
        fields = ('extracts', 'containers', 'extract_number',
                  'container_number', 'remove_deleted_children', 'message',
                  'introduction', 'conclusion', 'original_sha')

    def is_valid(self, raise_exception=False):
        error = not super(ChildrenListModifySerializer, self).is_valid(raise_exception)
        messages = {}
        if not self._validated_data['original_sha']:
            messages['original_sha'] = _("Vous n'avez pas fourni de marqueur de version")
            error = True
        if self._validated_data['original_sha'] != self.db_object.sha_draft:
            messages['original_sha'] = _("Quelqu'un a déjà édité le contenu pendant vous y travailliez.")
            error = True
        if error and raise_exception:
            self._errors.update(messages)
            raise ValidationError(self.errors)
        return not error

    def create(self, validated_data):
        return UpdateChildrenListViewModel(**validated_data)
