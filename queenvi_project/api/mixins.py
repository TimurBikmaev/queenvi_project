from rest_framework import serializers
from rest_framework.permissions import IsAuthenticatedOrReadOnly


# views.py
class HttpLookupMixin:
    http_method_names = ['get', 'post', 'patch', 'delete']
    lookup_field = 'public_id'
    permission_classes = [IsAuthenticatedOrReadOnly]


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
