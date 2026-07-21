from PIL import Image
from rest_framework import serializers

from user.constants import UserConstants as UC


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


class AvatarSerializerMixin(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()

    def get_avatar(self, obj):
        """Если юзер поставил свою аватарку, то твичовскую не выводим."""
        if obj.custom_avatar:
            return obj.custom_avatar
        return obj.twitch_avatar

    def validate_custom_avatar(self, image):
        """Проверка соответствия аватарки на допустимый размер и разрешение."""
        if image.size > UC.AVATAR_MAX_SIZE:
            raise serializers.ValidationError(
                f'Максимальный размер файла {UC.AVATAR_MAX_SIZE} МБ'
            )
        img = Image.open(image)
        if img.width > UC.AVATAR_MAX_WIDTH or img.height > UC.AVATAR_MAX_WIDTH:
            raise serializers.ValidationError(
                'Максимальное разрешение файла '
                f'{UC.AVATAR_MAX_WIDTH}x{UC.AVATAR_MAX_HEIGHT}'
            )
        return image

    def to_representation(self, obj):
        """Исключение null-полей из ответа сериализатора."""
        data = super().to_representation(obj)
        if obj.custom_avatar:
            del data['twitch_avatar']
        return {
            attr: value for attr, value in data.items()
            if value is not None
        }
