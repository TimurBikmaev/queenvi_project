from django.contrib.auth import get_user_model
from rest_framework import serializers

from api.constants import SerializersConstants
from api.mixins import AvatarSerializerMixin, BaseSerializerMixin
from post.constants import (
    CommentConstansts, MediaConstants as MC, PostConstants, ReportConstants
)
from post.errors import MediaFormatValidationError
from post.models import Comment, Media, Post, Report
from post.utils import MediaUtils
from youtube_suggestion.constants import VideoConstants
from youtube_suggestion.errors import (
    VideoAlreadyExistsError, VideoIdIncorrectError
)
from youtube_suggestion.models import Video
from youtube_suggestion.services import VideoSerivce


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
        fields = ['public_id', 'user', 'text', 'created_at']


class ShortMediaSerializer(serializers.ModelSerializer):
    """Превью поста."""
    class Meta:
        model = Media
        fields = ['file', 'file_type']


class MediaSerializer(ShortMediaSerializer):
    """Серилизатор медиа."""
    class Meta(ShortMediaSerializer.Meta):
        fields = ShortMediaSerializer.Meta.fields + ['order', 'created_at']


class ShortPostSerializer(BaseSerializerMixin):
    """Краткая информация о посте."""
    user = ShortUserSerializer(read_only=True)
    name = serializers.SerializerMethodField(read_only=True)
    description = serializers.SerializerMethodField(read_only=True)
    preview = serializers.SerializerMethodField(read_only=True)
    likes_count = serializers.ReadOnlyField()
    comments_count = serializers.ReadOnlyField()
    is_liked = serializers.BooleanField(read_only=True, default=False)

    class Meta:
        model = Post
        fields = [
            'public_id', 'user', 'name', 'description', 'preview',
            'likes_count', 'comments_count', 'is_liked', 'created_at'
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

    def get_preview(self, obj):
        preview = obj.preview_media[MC.PREVIEW_ORDER]
        return ShortMediaSerializer(preview, context=self.context).data

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
        max_length=SerializersConstants.POST_MEDIA_MAX_COUNT,
        write_only=True
    )
    list_media = MediaSerializer(
        source='media',
        many=True,
        read_only=True
    )

    class Meta(ShortPostSerializer.Meta):
        fields = [
            'public_id', 'user', 'name', 'description',
            'is_for_stream', 'likes_count', 'comments_count', 'is_liked',
            'create_media', 'list_media', 'comments', 'created_at'
        ]

    def check_media_data(self, files):
        try:
            media_data = MediaUtils.collect_media_data(files)
        except MediaFormatValidationError as e:
            raise serializers.ValidationError(str(e))
        return media_data

    def create(self, validated_data):
        files = validated_data.pop('create_media')
        media_data = self.check_media_data(files)
        post = Post.objects.create(**validated_data)
        Media.objects.bulk_create(
            Media(post=post, **data)
            for data in media_data
        )
        return post

    def update(self, instance, validated_data):
        files = validated_data.pop("create_media", None)
        if files is not None:
            media_data = self.check_media_data(files)
            instance.media.all().delete()
            MediaUtils.del_media_catalog(instance.public_id)
            instance = super().update(instance, validated_data)
            Media.objects.bulk_create(
                Media(post=instance, **data)
                for data in media_data
            )
            return instance


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
    user = ShortUserSerializer(read_only=True)

    class Meta:
        model = Video
        fields = [
            'public_id', 'youtube_url', 'youtube_id', 'user', 'title',
            'preview_url', 'channel_name', 'pub_date', 'duration',
            'views_count', 'likes_count', 'comments_count', 'category',
            'comment'
        ]
        read_only_fields = [
            'public_id', 'youtube_id', 'title', 'preview_url', 'channel_name',
            'pub_date', 'duration', 'views_count', 'likes_count',
            'comments_count',
        ]

    def create(self, validated_data):
        try:
            video = VideoSerivce.video_uploading(
                validated_data['youtube_url'],
                validated_data['user'],
                category=validated_data.get('category', ''),
                comment=validated_data.get('comment', '')
            )
        except (VideoAlreadyExistsError, VideoIdIncorrectError) as e:
            raise serializers.ValidationError(str(e))
        return video


class ModerationVideoSerializer(VideoSerializer):
    """Сериализатор видео для модерации."""

    class Meta(VideoSerializer.Meta):
        fields = VideoSerializer.Meta.fields + ['is_published']
        read_only_fields = VideoSerializer.Meta.read_only_fields
