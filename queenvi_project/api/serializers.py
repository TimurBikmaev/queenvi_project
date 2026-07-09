from django.contrib.auth import get_user_model
from rest_framework import serializers

from core.constants import BaseStatus
from post.models import Post


User = get_user_model()


class BaseSerializer(serializers.ModelSerializer):
    def to_representation(self, obj):
        """Исключение null-полей из ответа сериализатора."""
        data = super().to_representation(obj)
        return {
            attr: value for attr, value in data.items()
            if value is not None
        }


class UserSerializer(BaseSerializer):

    class Meta:
        model = User
        fields = [
            'id', 'username', 'avatar', 'is_active', 'role',
            'warnings', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'username',
                            'avatar', 'created_at', 'updated_at']


class ShortUserSerializer(BaseSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'avatar', 'created_at']
        read_only_fields = ['id', 'username', 'created_at']


class ProfilePostSerializer(BaseSerializer):
    class Meta:
        model = Post
        fields = ['id', 'name', 'is_for_stream', 'media', 'created_at']


class ProfileSerializer(BaseSerializer):
    posts_count = serializers.IntegerField(read_only=True)
    posts = ProfilePostSerializer(
        many=True, read_only=True, source='visible_posts'
    )

    class Meta:
        model = User
        fields = ['username', 'avatar', 'created_at', 'posts_count', 'posts']


class UpdateUserSerializer(BaseSerializer):

    class Meta:
        model = User
        fields = ['avatar']


# class PostSerializer(BaseSerializer):
#     user = ShortUserSerializer(read_only=True,
#                                #    is_null=False
#                                )

#     class Meta:
#         model = Post
#         fields = [
#             'name', 'is_for_stream', 'description',
#             'user', 'media', 'created_at', 'updated_at'
#         ]
