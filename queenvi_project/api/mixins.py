from rest_framework import serializers


# view.py
class HttpLookupMixin:
    http_method_names = ['get', 'post', 'patch', 'delete']
    lookup_field = 'public_id'


# serializers.py
class BaseSerializerMixin(serializers.ModelSerializer):
    def to_representation(self, obj):
        """Исключение null-полей из ответа сериализатора."""
        data = super().to_representation(obj)
        return {
            attr: value for attr, value in data.items()
            if value is not None
        }


class AvatarSerializerMixin:
    avatar_url = serializers.SerializerMethodField()

    def get_avatar_url(self, obj):
        if obj.avatar:
            return obj.avatar.url
        return obj.twitch_avatar_url
