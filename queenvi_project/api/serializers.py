from django.contrib.auth import get_user_model
from PIL import Image
from rest_framework import serializers

from api import mixins as mx
from api.constants import SerializersConstants as SC
from post import constants as cs
from post.errors import MediaFormatValidationError
from post.models import Comment, Media, Post, Report
from post.utils import MediaUtils
from user.constants import UserConstants as UC
from user.errors import ChangeUserValidationError
from user.validators import ChangeUserValidator as CUV
from youtube_suggestion import errors as er
from youtube_suggestion.constants import VideoConstants
from youtube_suggestion.models import Video
from youtube_suggestion.services import VideoSerivce


User = get_user_model()


class AvatarProfileSerializer(mx.BaseSerializerMixin):
    """Изменение автарки."""

    class Meta:
        model = User
        fields = ['twitch_avatar', 'custom_avatar']
        read_only_fields = ['twitch_avatar']

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
        """Если юзер поставил свою аватарку, то скрываем твичовскую."""
        data = super().to_representation(obj)
        if obj.custom_avatar:
            del data['twitch_avatar']
        return data


class ShortProfileSerializer(AvatarProfileSerializer):
    """Краткая информация профиля юзера."""

    class Meta(AvatarProfileSerializer.Meta):
        fields = AvatarProfileSerializer.Meta.fields + ['username']


class CommentSerializer(mx.BaseSerializerMixin):
    """Сериализатор комментария."""
    text = serializers.CharField(
        max_length=cs.CommentConstansts.TEXT_MAX_LENGTH
    )
    user = ShortProfileSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['public_id', 'user', 'text', 'created_at']


class PreviewMediaSerializer(mx.BaseSerializerMixin):
    """Превью поста."""
    class Meta:
        model = Media
        fields = ['file', 'file_type']


class MediaSerializer(PreviewMediaSerializer):
    """Серилизатор медиа."""
    class Meta(PreviewMediaSerializer.Meta):
        fields = PreviewMediaSerializer.Meta.fields + ['order', 'created_at']


class ShortPostSerializer(mx.PostSerializerMixin, mx.BaseSerializerMixin):
    """Краткая информация о посте."""
    user = ShortProfileSerializer(read_only=True)
    name = serializers.SerializerMethodField(read_only=True)
    description = serializers.SerializerMethodField(read_only=True)
    preview = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Post
        fields = SC.POST_BASE_FIELDS + ['preview']

    def get_name(self, obj):
        """Возвращает лишь первые несколько символов для название."""
        return obj.name[
            :SC.POST_PROFILE_NAME_MAX_LENGTH
        ]

    def get_description(self, obj):
        """Возвращает лишь первые несколько символов для описания."""
        return obj.description[
            :SC.POST_PROFILE_DESCRIPTION_MAX_LENGTH
        ]

    def get_preview(self, obj):
        preview = obj.preview_media[cs.MediaConstants.PREVIEW_ORDER]
        return PreviewMediaSerializer(preview, context=self.context).data


class ModerationShortPostSerializer(ShortPostSerializer):
    """Отображение части поста для модератора."""
    class Meta(ShortPostSerializer.Meta):
        fields = ShortPostSerializer.Meta.fields + ['is_banned']


class PostSerializer(ShortPostSerializer):
    """Подробная информация о посте."""
    name = serializers.CharField(
        max_length=cs.PostConstants.NAME_MAX_LENGTH
    )
    description = serializers.CharField(
        max_length=cs.PostConstants.DESCRIPTION_MAX_LENGTH,
        required=False,
        allow_blank=True
    )
    comments = CommentSerializer(many=True, read_only=True)
    create_media = serializers.ListField(
        child=serializers.FileField(),
        min_length=SC.POST_MEDIA_MIN_COUNT,
        max_length=SC.POST_MEDIA_MAX_COUNT,
        write_only=True
    )
    list_media = MediaSerializer(
        source='media',
        many=True,
        read_only=True
    )

    class Meta(ShortPostSerializer.Meta):
        fields = SC.POST_BASE_FIELDS + [
            'create_media', 'list_media', 'comments',
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
        files = validated_data.pop('create_media', None)
        if files is not None:
            media_data = self.check_media_data(files)
            instance.media.all().delete()
            MediaUtils.del_media_catalog(instance.public_id)
            Media.objects.bulk_create(
                Media(post=instance, **data)
                for data in media_data
            )
        return super().update(instance, validated_data)


class ModerationPostSerializer(mx.PostSerializerMixin, mx.BaseSerializerMixin):
    """Отображение и редактирование поста для модератора."""
    user = ShortProfileSerializer(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    list_media = MediaSerializer(
        source='media',
        many=True,
        read_only=True
    )

    class Meta(ModerationShortPostSerializer.Meta):
        fields = SC.POST_BASE_FIELDS + [
            'list_media', 'comments', 'is_banned', 'updated_at'
        ]
        read_only_fields = [
            'public_id', 'name', 'description', 'is_for_stream'
        ]


class ProfileSerializer(ShortProfileSerializer):
    """Профиль для обычного юзера."""
    posts_count = serializers.ReadOnlyField()
    posts = ShortPostSerializer(
        many=True,
        source='visible_posts',
        read_only=True
    )

    class Meta(ShortProfileSerializer.Meta):
        fields = ShortProfileSerializer.Meta.fields + [
            'posts_count', 'posts', 'created_at'
        ]


class ModerationSteamerProfileSerializer(ProfileSerializer):
    """Профиль юзера для модерации и стримера."""
    class Meta(ProfileSerializer.Meta):
        fields = ProfileSerializer.Meta.fields + [
            'is_active', 'role', 'updated_at'
        ]
        read_only_fields = ['username', 'twitch_avatar', 'custom_avatar']

    def update(self, instance, validated_data):
        user = self.context['request'].user
        role = validated_data.get('role')
        try:
            CUV.user_cannot_change_himself(user, self.instance)
            if role:
                CUV.can_user_change_role(user)
                CUV.only_one_streamer(user, role)
            if 'is_active' in validated_data:
                CUV.can_user_change_is_active(user, self.instance)
        except ChangeUserValidationError as e:
            raise serializers.ValidationError(str(e))
        return super().update(instance, validated_data)


class CreateReportSerializer(mx.BaseSerializerMixin):
    """Сериализатор жалобы."""
    other = serializers.CharField(
        max_length=cs.ReportConstants.OTHER_MAX_LENGTH,
        required=False,
        allow_blank=True
    )

    class Meta:
        model = Report
        fields = ['reason', 'other', 'user', 'post']
        read_only_fields = ['user', 'post']

    def create(self, validated_data):
        post = validated_data.get('post')
        if not post.user.is_user:
            raise serializers.ValidationError(
                cs.ReportConstants.MSG_CANNOT_REPORT_STAFF
            )
        return super().create(validated_data)

    def to_representation(self, obj):
        """При создании жалобы юзера прост возвращается сообщение."""
        return {
            'message': cs.ReportConstants.MSG_CREATED.format(
                public_id=obj.public_id
            )
        }


class ModerationReportSerializer(mx.BaseSerializerMixin):
    """Сериализатор жалобы для модерации."""
    user = serializers.SerializerMethodField(read_only=True)
    post = serializers.SerializerMethodField(read_only=True)
    moderator = serializers.SerializerMethodField(read_only=True)

    class Meta(CreateReportSerializer.Meta):
        fields = CreateReportSerializer.Meta.fields + [
            'public_id', 'status', 'moderator', 'created_at', 'updated_at'
        ]
        read_only_fields = CreateReportSerializer.Meta.fields + [
            'public_id', 'moderator'
        ]

    def update(self, instance, validated_data):
        status = validated_data.get('status')
        instance = super().update(instance, validated_data)
        if status == cs.ReportStatus.APPROVED:
            instance.post.is_banned = True
            instance.post.save(update_fields=['is_banned'])
        elif status == cs.ReportStatus.REJECTED:
            instance.post.is_banned = False
            instance.post.save(update_fields=['is_banned'])
        instance.moderator = self.context['request'].user
        instance.save()
        return instance

    def get_user(self, obj):
        """Возвращаем юзернейм того, кто кинул репорт."""
        return obj.user.username

    def get_post(self, obj):
        """Возвращаем public_id поста, который зарепортили."""
        return obj.post.public_id

    def get_moderator(self, obj):
        """Возвращаем юзернейм модератора, который рассмотрел репорт."""
        if obj.moderator is not None:
            return obj.moderator.username

    def validate_status(self, value):
        """Если репорт рассмотрен, то поменять статус на not_viewed нельзя."""
        if value == cs.ReportStatus.NOT_VIEWED:
            raise serializers.ValidationError(
                cs.ReportConstants.MSG_STATUS_TO_NOT_VIEWED
            )
        return value


class VideoSerializer(mx.VideoSerializerMixin, mx.BaseSerializerMixin):
    """Сериализатор видео."""
    youtube_url = serializers.URLField(write_only=True)
    comment = serializers.CharField(
        max_length=VideoConstants.COMMENT_MAX_LENGTH
    )
    user = ShortProfileSerializer(read_only=True)

    class Meta:
        model = Video
        fields = SC.VIDEO_BASE_FIELDS + ['youtube_url']
        read_only_fields = [
            'public_id', 'youtube_id', 'title', 'preview_url', 'channel_name',
            'pub_date', 'duration', 'views_count', 'likes_count',
            'comments_count'
        ]

    def create(self, validated_data):
        try:
            video = VideoSerivce.video_uploading(
                validated_data['youtube_url'],
                validated_data['user'],
                category=validated_data.get('category', ''),
                comment=validated_data.get('comment', '')
            )
        except (er.VideoAlreadyExistsError, er.VideoIdIncorrectError) as e:
            raise serializers.ValidationError(str(e))
        return video

    def update(self, instance, validated_data):
        if self.context['request'].user.is_user and instance.is_banned:
            raise serializers.ValidationError(
                VideoConstants.MSG_CANNOT_CHANGE_BANNED
            )
        return super().update(instance, validated_data)


class ModerationVideoSerializer(
    mx.VideoSerializerMixin, mx.BaseSerializerMixin
):
    """Сериализатор видео для модерации."""
    user = ShortProfileSerializer(read_only=True)

    class Meta(VideoSerializer.Meta):
        fields = SC.VIDEO_BASE_FIELDS + ['is_banned', 'updated_at']
        read_only_fields = VideoSerializer.Meta.read_only_fields + [
            'category', 'comment'
        ]
