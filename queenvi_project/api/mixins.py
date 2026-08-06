from rest_framework import mixins as mx, serializers


# views.py
class HttpLookupMixin:
    http_method_names = ['get', 'post', 'patch', 'delete']
    lookup_field = 'public_id'


class ListUpdateMixin(mx.ListModelMixin, mx.UpdateModelMixin):
    pass


# serializers.py
class BaseSerializerMixin(serializers.ModelSerializer):
    public_id = serializers.ReadOnlyField()

    def to_representation(self, obj):
        """Исключение null-полей и пустых строк из ответа сериализатора."""
        data = super().to_representation(obj)
        return {
            attr: value for attr, value in data.items()
            if value is not None and value != ''
        }


class VideoSerializerMixin:
    is_voted = serializers.ReadOnlyField()
    votings_count = serializers.ReadOnlyField()
