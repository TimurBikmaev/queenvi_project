import logging

from rest_framework import mixins as mx, serializers

from core.errors import ChangeObjValidationError
from core.validators import ChangeBanStatusValidator as CBSV


logger = logging.getLogger(__name__)


class HttpLookupMixin:
    http_method_names = ['get', 'post', 'patch', 'delete']
    lookup_field = 'public_id'


class ListUpdateMixin(mx.ListModelMixin, mx.UpdateModelMixin):
    pass


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


class UpdateBanSerializerMixin:
    def update(self, instance, validated_data):
        user = self.context['request'].user
        is_banned = validated_data.get('is_banned')

        try:
            CBSV.cannot_change_streamer_obj(instance, user)
            if is_banned is not None and is_banned is False:
                CBSV.cannot_unban_obj_of_banned_user(instance, user)
        except ChangeObjValidationError as e:
            raise serializers.ValidationError(str(e))

        old_is_banned = instance.is_banned
        obj = super().update(instance, validated_data)

        if is_banned is not None:
            logger.info(
                'Юзер %s (%s) изменил статус бана объекта %s (%s) c %s на %s',
                user.username,
                user.role,
                instance.public_id,
                instance.id,
                old_is_banned,
                is_banned
            )

        return obj
