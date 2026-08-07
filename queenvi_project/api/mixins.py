from rest_framework import mixins as mx, serializers

from core.errors import ChangeObjValidationError
from core.validators import ChangeBanStatusValidator as CBSV


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


class UpdateBanMixin:
    def update(self, instance, validated_data):
        is_banned = validated_data.get('is_banned')
        try:
            CBSV.cannot_change_streamer_obj(instance)
            if is_banned is not None and is_banned is False:
                CBSV.cannot_unban_obj_of_banned_user(instance)
        except ChangeObjValidationError as e:
            raise serializers.ValidationError(str(e))
        return super().update(instance, validated_data)
