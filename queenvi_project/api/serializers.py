from django.contrib.auth import get_user_model
from rest_framework import serializers

from post.models import Post


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['id', 'twitch_id', 'username', 'avatar', 'role', 'warnings']
        read_only_fields = ['twitch_id', 'username', 'avatar']


class ShortUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'avatar']
        read_only_fields = ['username']


class CreateUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['twitch_id', 'avatar']

    def create(self, validated_data):
        user = User(**validated_data)
        user.set_unusable_password()
        user.username = validated_data['twitch_id']
        user.save()
        return user


class UpdateUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['avatar']


class PostSerializer(serializers.ModelSerializer):
    user = UserShortSerializer(read_only=True)

    class Meta:
        model = Post
        fields = [
            'name', 'description', 'is_for_stream',
            'user', 'created_at', 'updated_at'
        ]
