from rest_framework import serializers
from rest_framework.relations import ManyRelatedField, PrimaryKeyRelatedField


class ZdSModelSerializer(serializers.ModelSerializer):
    def get_fields(self):
        fields = super().get_fields()

        request = self._context.get("request")
        if request is None:
            return fields

        expands = request.GET.getlist("expand")
        if expands:
            fields = self._update_expand_fields(fields, expands)

        x_data_format = request.META.get("HTTP_X_DATA_FORMAT") or "Markdown"
        if hasattr(self.Meta, "formats"):
            fields = self._update_format_fields(fields, x_data_format)

        return fields

    def _update_expand_fields(self, fields, expands):
        assert hasattr(
            self.Meta, "serializers"
        ), 'Class {serializer_class} missing "Meta.serializers" attribute'.format(
            serializer_class=self.__class__.__name__
        )

        dict_serializers = dict()
        for serializer in self.Meta.serializers:
            dict_serializers[serializer.Meta.model] = serializer

        for expand in expands:
            field = fields.get(expand)
            args = {}
            current_serializer = None

            try:
                if isinstance(field, PrimaryKeyRelatedField):
                    current_serializer = dict_serializers[field.queryset.model]
                elif isinstance(field, ManyRelatedField):
                    current_serializer = dict_serializers[field.child_relation.queryset.model]
                    args = {"many": True}

                assert (
                    current_serializer is not None
                ), "You cannot expand a field without a serializer of the same model."
            except KeyError:
                continue

            fields[expand] = current_serializer(**args)

        return fields

    def _update_format_fields(self, fields, x_data_format="Markdown"):
        assert hasattr(self.Meta, "formats"), 'Class {serializer_class} missing "Meta.formats" attribute'.format(
            serializer_class=self.__class__.__name__
        )

        for current in self.Meta.formats:
            if current != x_data_format:
                fields.pop(self.Meta.formats[current])

        return fields
