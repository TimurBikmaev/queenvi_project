from django.contrib.auth import get_user_model
from rest_framework import serializers

from api.constants import SerializersConstants
from api.utils import file_extension_revealing
from api.mixins import AvatarSerializerMixin, BaseSerializerMixin
from post.constants import CommentConstansts, PostConstants, ReportConstants
from post.models import Comment, Like, Media, Post, Report
from youtube_suggestion.constants import VideoConstants
from youtube_suggestion.models import Video


User = get_user_model()


class ShortUserSerializer(AvatarSerializerMixin):
    """Краткая информация о юзере."""

    class Meta:
        model = User
        fields = ['username', 'twitch_avatar', 'custom_avatar']


class CommentSerializer(BaseSerializerMixin):
    """Сериализатор комментария."""
    text = serializers.CharField(
        max_length=CommentConstansts.TEXT_MAX_LENGTH
    )
    user = ShortUserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['public_id', 'user', 'text', 'updated_at']


class MediaSerializer(serializers.ModelSerializer):
    """Серилизатор медиа."""
    class Meta:
        model = Media
        fields = ['file', 'type_of_file', 'created_at']


class ShortPostSerializer(BaseSerializerMixin):
    """Краткая информация о посте."""
    user = ShortUserSerializer(read_only=True)
    name = serializers.SerializerMethodField(read_only=True)
    description = serializers.SerializerMethodField(read_only=True)
    # Только первый файл (methodfield).
    one_media = MediaSerializer(many=True, read_only=True)
    likes_count = serializers.ReadOnlyField(read_only=True)
    comments_count = serializers.ReadOnlyField(read_only=True)

    class Meta:
        model = Post
        fields = [
            'public_id', 'user', 'name', 'description',  'one_media',
            'likes_count', 'comments_count', 'created_at',
        ]

    def get_name(self, obj):
        """Возвращает лишь первые несколько символов для название."""
        return obj.name[
            :SerializersConstants.POST_PROFILE_NAME_MAX_LENGTH
        ]

    def get_description(self, obj):
        """Возвращает лишь первые несколько символов для описания."""
        return obj.description[
            :SerializersConstants.POST_PROFILE_DESCRIPTION_MAX_LENGTH
        ]

    def to_representation(self, obj):
        """Если в описании пустая строка, скрываем его."""
        data = super().to_representation(obj)
        if data['description'] == '':
            del data['description']
        return data


class PostSerializer(ShortPostSerializer):
    """Сериализатор поста."""
    name = serializers.CharField(
        max_length=PostConstants.NAME_MAX_LENGTH
    )
    description = serializers.CharField(
        max_length=PostConstants.DESCRIPTION_MAX_LENGTH,
        required=False,
        allow_blank=True
    )
    comments = CommentSerializer(many=True, read_only=True)
    create_media = serializers.ListField(
        child=serializers.FileField(),
        min_length=SerializersConstants.POST_MEDIA_MIN_COUNT,
        write_only=True
    )
    list_media = MediaSerializer(
        source='media',
        many=True,
        read_only=True
    )

    class Meta(ShortPostSerializer.Meta):
        fields = ShortPostSerializer.Meta.fields + [
            'is_for_stream', 'create_media', 'list_media', 'comments'
        ]

    def create(self, validated_data):
        files = validated_data.pop('media')
        post = Post.objects.create(**validated_data)
        for file in files:
            file_extenstion = file_extension_revealing(file)
            Media.objects.create(
                post=post,
                file=file,
                type_of_file=file_extenstion
            )
        return post


class ModerationPostSerializer(PostSerializer):
    """Отображение и редактирования поста для модератора."""
    class Meta(PostSerializer.Meta):
        fields = PostSerializer.Meta.fields + ['status']


class UserSerializer(AvatarSerializerMixin, BaseSerializerMixin):
    """Сериализатор юзера."""
    posts_count = serializers.ReadOnlyField()
    posts = ShortPostSerializer(
        many=True,
        source='visible_posts',
        read_only=True
    )

    class Meta(ShortUserSerializer.Meta):
        fields = ShortUserSerializer.Meta.fields + [
            'posts_count', 'posts', 'created_at'
        ]
        read_only_fields = ['username']


class ModerationUserSerializer(UserSerializer):
    """Сериалиазтор юзера для модерации."""
    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + [
            'is_active', 'role', 'warnings', 'updated_at'
        ]
        read_only_fields = ['username', 'twitch_avatar', 'custom_avatar']


class ReportSerializer(BaseSerializerMixin):
    """Сериализатор жалобы."""
    text = serializers.CharField(
        max_length=ReportConstants.REASON_MAX_LENGTH,
    )

    class Meta:
        model = Report
        fields = ['public_id', 'text', 'user', 'post', 'created_at']
        read_only_fields = ['user', 'post']


class VideoSerializer(BaseSerializerMixin):
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
            'public_id', 'youtube_url', 'user', 'name', 'preview',
            'channel_name', 'duration', 'pub_date', 'category', 'comment'
        ]
        read_only_fields = [
            'user', 'name', 'preview', 'channel_name', 'duration', 'pub_date'
        ]
