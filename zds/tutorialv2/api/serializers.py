import copy
import datetime
import logging
from collections import Counter

import uuslug
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, empty

from zds.tutorialv2.api.view_models import ChildrenViewModel, ChildrenListViewModel, UpdateChildrenListViewModel
from django.utils.translation import ugettext as _

from zds.tutorialv2.models.database import PublishableContent
from zds.tutorialv2.utils import init_new_repo
from zds.utils.forms import TagValidator
from zds.utils.models import SubCategory

logger = logging.getLogger(__name__)


class CommaSeparatedCharField(CharField):
    """
    Allows to transform a list of objects into comma separated list and vice versa
    """
    def __init__(self, *, filter_function=None, **kwargs):
        super().__init__(**kwargs)
        self.filter_method = filter_function

    def __deepcopy__(self, memodict):
        args = []
        kwargs = {
            key: (copy.deepcopy(value) if (key not in ('validators', 'regex', 'filter_function')) else value)
            for key, value in self._kwargs.items()
        }
        return self.__class__(*args, **kwargs)

    def to_internal_value(self, data):
        if isinstance(data, (list, tuple)):
            return super().to_internal_value(','.join(str(value) for value in data))
        return super().to_internal_value(data)

    def run_validation(self, data=empty):
        validated_string = super().run_validation(data)
        if data == '':
            return []
        return list(filter(self.filter_method, validated_string.split(',')))


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
                logger.warning('Error translated from %s to %s', exception1, exception2(message))
                raise exception2(message)
        return decorated
    return wrapper


class ChildrenSerializer(serializers.Serializer):
    text = serializers.CharField(allow_blank=True, allow_null=False, required=False, default='')

    class Meta:
        model = ChildrenViewModel
        fields = ('child_type', 'title', 'description', 'text')


class ChildrenListSerializer(serializers.Serializer):
    """
    Serialize children list so that api can handle them
    """

    extracts = serializers.ListField(child=ChildrenSerializer())
    containers = serializers.ListField(child=ChildrenSerializer())
    extract_number = serializers.IntegerField(source='extracts.__len__')
    container_number = serializers.IntegerField(source='containers.__len__')
    introduction = serializers.CharField(required=False, default='', allow_null=False)
    conclusion = serializers.CharField(required=False, default='', allow_null=False)

    class Meta:
        fields = ('extracts', 'containers', 'extract_number', 'container_number',
                  'introduction', 'conclusion')

    def __init__(self, *args, **kwargs):
        self.db_object = kwargs.pop('db_object', None)
        super().__init__(*args, **kwargs)
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

        has_error = not super().is_valid(raise_exception)  # yes, this boolean is not mandatory but it allows us
        # to write elegant condition such as if has_errors so it's more readable with that.
        messages = {}

        for field_name, value in self.initial_data.items():
            if field_name in self.Meta.fields:
                self._validated_data[field_name] = value
        if self._validated_data.get('extracts', None):
            self._validated_data['extracts'] = [ChildrenViewModel(**v) for v in self._validated_data['extracts']]
            has_error = self.validate_extracts_structure(has_error, messages)
        if self.initial_data.get('containers', None):
            self._validated_data['containers'] = [ChildrenViewModel(**v) for v in self._validated_data['containers']]
            has_error = self.validate_container_structure(has_error, messages)
        self._validated_data['conclusion'] = self.initial_data.get('conclusion', '')
        if not self._validated_data['extracts'] and not self._validated_data['containers']:
            has_error = True
            messages['extracts'] = _('Le contenu semble vide.')
        if raise_exception and has_error:
            self._errors.update(messages)
            raise ValidationError(self.errors)

        return not has_error

    def validate_container_structure(self, has_error, messages):
        if len(self._validated_data['containers']) != len(set(e.title for e in self._validated_data['containers'])):
            has_error = True
            titles = Counter(list(e.title for e in self._validated_data['containers']))
            doubly = [key for key, v in titles.items() if v > 1]
            messages['containers'] = _('Certaines parties ou chapitres sont en double : {}').format(','.join(doubly))
        if not all(c.child_type.lower() == 'container' for c in self._validated_data.get('containers', [])):
            has_error = True
            messages['containers'] = _('Un conteneur est mal configuré')
        self._validated_data['introduction'] = self.initial_data.get('introduction', '')
        return has_error

    def validate_extracts_structure(self, has_error, messages):
        if not all(c.child_type.lower() == 'extract' for c in self._validated_data.get('extracts', [])):
            has_error = True
            messages['extracts'] = _('un extrait est mal configuré')
        if len(self._validated_data['extracts']) != len(set(e.title for e in self._validated_data['extracts'])):
            has_error = True
            titles = Counter(list(e.title for e in self._validated_data['extracts']))
            doubly = [key for key, v in titles.items() if v > 1]
            messages['extracts'] = _('Certains titres sont en double : {}').format(','.join(doubly))
        return has_error

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
    remove_deleted_children = serializers.BooleanField()
    message = serializers.CharField(required=False)
    original_sha = serializers.CharField(required=False, default='', allow_null=False)

    class Meta:
        model = UpdateChildrenListViewModel
        fields = ('extracts', 'containers', 'extract_number',
                  'container_number', 'remove_deleted_children', 'message',
                  'introduction', 'conclusion', 'original_sha')

    def is_valid(self, raise_exception=False):
        error = not super().is_valid(raise_exception)
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


class PublishableMetaDataSerializer(serializers.ModelSerializer):
    tags = CommaSeparatedCharField(required=False, filter_function=TagValidator().validate_one_element)

    class Meta:
        model = PublishableContent
        exclude = ('is_obsolete', 'must_reindex', 'last_note', 'helps', 'beta_topic', 'image')
        read_only_fields = ('authors', 'gallery', 'public_version', 'is_locked', 'relative_images_path',
                            'sha_picked', 'sha_draft', 'sha_validation', 'sha_beta', 'sha_public', 'picked_date',
                            'update_date', 'pubdate', 'creation_date', 'slug')
        depth = 2

    def create(self, validated_data):
        # default db values
        validated_data['js_support'] = False  # Always false when we create
        validated_data['creation_date'] = datetime.datetime.now()

        # links to other entities
        tags = validated_data.pop('tags', '')
        content = super().create(validated_data)
        content.save()
        content.add_tags(tags)
        init_new_repo(content, '', '', _('Création de {}').format(content.title), do_commit=True)
        content.authors.add(self.context['author'])
        content.create_gallery()
        content.save()
        content.ensure_author_gallery()
        return content

    def update(self, instance, validated_data):
        working_dictionary = copy.deepcopy(validated_data)
        versioned = instance.load_version()
        must_save_version = False
        if working_dictionary.get('tags', []):
            instance.replace_tags(working_dictionary.pop('tags'))
        if working_dictionary.get('title', instance.title) != instance.title:
            instance.title = working_dictionary.pop('title')
            instance.slug = uuslug(instance.title, instance=instance, max_length=80)
            versioned.title = instance.title
            versioned.slug = instance.slug
            must_save_version = True
        if working_dictionary.get('type', instance.type) != instance.type:
            instance.type = working_dictionary.pop('type')
            versioned.type = instance.type
            must_save_version = True
        if must_save_version:
            instance.sha_draft = versioned.repo_update(
                title=instance.title,
                introduction=versioned.get_introduction(),
                conclusion=versioned.get_conclusion(),
                do_commit=True
            )
        return super.update(instance, working_dictionary)


class ContentCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCategory
        depth = 1
