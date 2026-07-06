from django.contrib.auth import get_user_model
from rest_framework import serializers


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['twitch_id', 'avatar', 'role', 'warnings']
        read_only_fields = ['twitch_id']

    def create(self, validated_data):
        user = User(**validated_data)
        user.set_unusable_password()
        user.username = validated_data['twitch_id']
        user.save()
        return user
