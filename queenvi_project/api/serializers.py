from django.contrib.auth import get_user_model
from rest_framework import serializers

from api.constants import SerializersConstants
from post.constants import CommentConstansts, PostConstants, ReportConstants
from post.models import Comment, Post, Report
from youtube_suggestion.constants import VideoConstants
from youtube_suggestion.models import Video


User = get_user_model()


class BaseSerializer(serializers.ModelSerializer):
    def to_representation(self, obj):
        """Исключение null-полей из ответа сериализатора."""
        data = super().to_representation(obj)
        return {
            attr: value for attr, value in data.items()
            if value is not None
        }


class ShortUserSerializer(BaseSerializer):
    """Краткая информация о юзере."""
    class Meta:
        model = User
        fields = ['id', 'username', 'avatar']


class CommentSerializer(BaseSerializer):
    """Сериализатор комментария."""
    text = serializers.CharField(
        max_length=CommentConstansts.TEXT_MAX_LENGTH
    )
    user = ShortUserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'user', 'text', 'updated_at']


class ShortPostSerializer(BaseSerializer):
    """Краткая информация о посте."""
    user = ShortUserSerializer()
    description = serializers.SerializerMethodField()
    media = ...  # Только первый файл (methodfield).
    likes_count = ...
    comments_count = ...

    class Meta:
        model = Post
        fields = [
            'id', 'user', 'name', 'description', 'media',
            'is_for_stream', 'likes_count', 'comments_count', 'updated_at',
        ]

    def get_description(self, obj):
        return obj.description[
            :SerializersConstants.POST_PROFILE_DESCRIPTION_MAX_LENGTH
        ]


class PostSerializer(ShortPostSerializer):
    """Сериализатор поста."""
    name = serializers.CharField(
        max_length=PostConstants.NAME_MAX_LENGTH
    )
    description = serializers.CharField(
        max_length=PostConstants.DESCRIPTION_MAX_LENGTH
    )
    comments = CommentSerializer(many=True)

    class Meta(ShortPostSerializer.Meta):
        fields = ShortPostSerializer.Meta.fields + ['comments']
        read_only_fields = ['user', 'likes_count', 'comments_count']


class ModerationPostSerializer(PostSerializer):
    """Отображение и редактирования поста для модератора."""
    class Meta(PostSerializer.Meta):
        fields = PostSerializer.Meta.fields + ['status']


class UserSerializer(BaseSerializer):
    """Сериализатор юзера."""
    posts_count = serializers.IntegerField()
    posts = ShortPostSerializer(many=True, source='visible_posts')

    class Meta(ShortUserSerializer.Meta):
        fields = ShortUserSerializer.Meta.fields + [
            'posts_count', 'posts', 'created_at'
        ]
        read_only_fields = ['username', 'posts_count', 'posts']


class ModerationUserSerializer(UserSerializer):
    """Сериалиазтор юзера для модерации."""
    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + [
            'is_active', 'role', 'warnings', 'updated_at'
        ]
        read_only_fields = UserSerializer.Meta.read_only_fields + [
            'avatar'
        ]


class ReportSerializer(BaseSerializer):
    """Сериализатор жалобы."""
    text = serializers.CharField(
        max_length=ReportConstants.REASON_MAX_LENGTH,
    )

    class Meta:
        model = Report
        fields = ['id', 'text', 'user', 'post', 'created_at']
        read_only_fields = ['user', 'post']


class VideoSerializer(BaseSerializer):
    """Сериализатор видео."""
    youtube_url = serializers.URLField(write_only=True)
    comment = serializers.CharField(
        max_length=VideoConstants.COMMENT_MAX_LENGTH
    )
    name = serializers.CharField(
        max_length=VideoConstants.NAME_MAX_LENGTH
    )
    preview = serializers.CharField(
        max_length=VideoConstants.PREVIEW_MAX_LENGTH
    )
    channel_name = serializers.CharField(
        max_length=VideoConstants.CHANNEL_NAME_MAX_LENGTH
    )
    user = ShortUserSerializer()

    class Meta:
        model = Video
        fields = [
            'id', 'youtube_url', 'user', 'name', 'preview',
            'channel_name', 'duration', 'pub_date', 'category', 'comment'
        ]
        read_only_fields = [
            'user', 'name', 'preview', 'channel_name', 'duration', 'pub_date'
        ]
