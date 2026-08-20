import logging

from django.contrib.auth import get_user_model
from drf_spectacular import utils as swg
from PIL import Image
from rest_framework import serializers

from api import mixins as mx
from api.constants import SerializersConstants as SC
from post import constants as cs
from post.errors import MediaFormatValidationError
from post.models import Comment, Media, Post, Report
from post.utils import MediaUtils
from user.constants import UserConstants as UC, UserRole
from user.errors import ChangeUserValidationError
from user.validators import ChangeUserValidator as CUV
from youtube_suggestion import errors as er
from youtube_suggestion.constants import (
    Category, CategoryConstants, VideoConstants
)
from youtube_suggestion.models import Video
from youtube_suggestion.services import VideoSerivce


logger = logging.getLogger(__name__)
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
            logger.warning(
                'Кастомная авка у юзера %s превышает размер: %s > %s',
                self.instance.username,
                image.size,
                UC.AVATAR_MAX_SIZE,
            )
            raise serializers.ValidationError(UC.MSG_SIZE)

        img = Image.open(image)
        if (
            img.width > UC.AVATAR_MAX_WIDTH
            or img.height > UC.AVATAR_MAX_HEIGHT
        ):
            logger.warning(
                'Кастомная авка у юзера %s превышает разрешение: '
                '%sx%s > %sx%s',
                self.instance.username,
                img.width,
                img.height,
                UC.AVATAR_MAX_WIDTH,
                UC.AVATAR_MAX_HEIGHT,
            )
            raise serializers.ValidationError(UC.MSG_RESOLUTION)

        return image

    def to_representation(self, obj):
        """Если юзер поставил свою аватарку, то скрываем твичовскую."""
        data = super().to_representation(obj)

        if obj.custom_avatar:
            del data['twitch_avatar']

        return data


@swg.extend_schema_serializer(exclude_fields='twitch_avatar')
class ShortProfileSerializer(AvatarProfileSerializer):
    """Краткая информация профиля юзера."""
    username = serializers.SerializerMethodField()

    class Meta(AvatarProfileSerializer.Meta):
        fields = AvatarProfileSerializer.Meta.fields + ['username']

    @swg.extend_schema_field(str)
    def get_username(self, obj):
        return obj.username


class CommentSerializer(mx.BaseSerializerMixin):
    """Сериализатор комментария."""
    text = serializers.CharField(
        max_length=cs.CommentConstansts.TEXT_MAX_LENGTH
    )
    user = ShortProfileSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['public_id', 'user', 'text', 'created_at', 'updated_at']


class PreviewMediaSerializer(mx.BaseSerializerMixin):
    """Превью поста."""
    file_type = serializers.SerializerMethodField()

    class Meta:
        model = Media
        fields = ['file', 'file_type']

    @swg.extend_schema_field(str)
    def get_file_type(self, obj):
        return obj.file_type


class MediaSerializer(PreviewMediaSerializer):
    """Серилизатор медиа."""
    order = serializers.SerializerMethodField()

    class Meta(PreviewMediaSerializer.Meta):
        fields = PreviewMediaSerializer.Meta.fields + ['order', 'created_at']

    @swg.extend_schema_field(int)
    def get_order(self, obj):
        return obj.order


class ShortPostSerializer(mx.BaseSerializerMixin):
    """Краткая информация о посте."""
    user = ShortProfileSerializer(read_only=True)
    name = serializers.SerializerMethodField(read_only=True)
    description = serializers.SerializerMethodField(read_only=True)
    preview = serializers.SerializerMethodField(read_only=True)
    likes_count = serializers.IntegerField(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = SC.POST_BASE_FIELDS + ['preview']

    def get_name(self, obj) -> str:
        """Возвращает лишь первые несколько символов для название."""
        return obj.name[:cs.PostConstants.NAME_PROFILE_MAX_LENGTH]

    def get_description(self, obj) -> str:
        """Возвращает лишь первые несколько символов для описания."""
        return obj.description[
            :cs.PostConstants.DESCRIPTION_PROFILE_MAX_LENGTH
        ]

    def get_preview(self, obj) -> PreviewMediaSerializer:
        preview = obj.preview_media[cs.MediaConstants.PREVIEW_ORDER]
        return PreviewMediaSerializer(preview, context=self.context).data

    @swg.extend_schema_field({
        'type': 'boolean',
        'example': False,
    })
    def get_is_liked(self, obj):
        return obj.is_liked


class SearchPostSerializer(mx.BaseSerializerMixin):
    """Краткая информация о посте в поиске."""
    user = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField(read_only=True)
    preview = serializers.SerializerMethodField(read_only=True)

    class Meta(ShortPostSerializer.Meta):
        fields = ['public_id', 'name', 'preview', 'user',]

    def get_name(self, obj) -> str:
        """Возвращает лишь первые несколько символов для название."""
        return obj.name[:cs.PostConstants.NAME_PROFILE_MAX_LENGTH]

    def get_preview(self, obj) -> PreviewMediaSerializer:
        preview = obj.preview_media[cs.MediaConstants.PREVIEW_ORDER]
        return PreviewMediaSerializer(preview, context=self.context).data

    def get_user(self, obj) -> str:
        return obj.user.username


class SearchSerializer(serializers.Serializer):
    """Краткая информация о посте в поиске."""
    users = ShortProfileSerializer(many=True)
    posts = SearchPostSerializer(many=True)


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
    create_media = serializers.ListField(
        child=serializers.FileField(),
        min_length=cs.PostConstants.MEDIA_MIN_COUNT,
        max_length=cs.PostConstants.MEDIA_MAX_COUNT,
        write_only=True
    )
    media = MediaSerializer(
        many=True,
        read_only=True,
        source='list_media',
    )

    class Meta(ShortPostSerializer.Meta):
        fields = SC.POST_BASE_FIELDS + ['create_media', 'media']

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

        post.likes_count = cs.PostConstants.NO_LIKES
        post.comments_count = cs.PostConstants.NO_COMMENTS
        post.is_liked = False
        post.list_media = Media.objects.bulk_create(
            Media(post=post, **data)
            for data in media_data
        )

        logger.info(
            'Юзер %s (%s) создал пост %s',
            post.user.username,
            post.user.role,
            post.public_id
        )

        return post

    def update(self, instance, validated_data):
        name = validated_data.get('name')
        description = validated_data.get('description')
        is_for_stream = validated_data.get('is_for_stream')
        files = validated_data.pop('create_media', None)

        changes = {}

        if name is not None:
            changes['name'] = (instance.name, name)
        if description is not None:
            changes['description'] = (instance.description, description)
        if is_for_stream is not None:
            changes['is_for_stream'] = (instance.is_for_stream, is_for_stream)

        if files is not None:
            media_data = self.check_media_data(files)
            changes['media'] = ('Изменены медиа поста')

            instance.media.all().delete()
            MediaUtils.del_media_catalog(instance.public_id)

            Media.objects.bulk_create(
                Media(post=instance, **data)
                for data in media_data
            )

        post = super().update(instance, validated_data)

        logger.info(
            'Юзер %s (%s) обновил пост %s: %s',
            post.user.username,
            post.user.role,
            post.public_id,
            changes
        )
        return post


class ModerationPostSerializer(
    mx.UpdateBanSerializerMixin, mx.BaseSerializerMixin
):
    """Отображение и редактирование поста для модератора."""
    user = ShortProfileSerializer(read_only=True)
    media = MediaSerializer(
        source='list_media',
        many=True,
        read_only=True
    )
    likes_count = serializers.IntegerField(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)
    is_liked = serializers.BooleanField(read_only=True)

    class Meta(ModerationShortPostSerializer.Meta):
        fields = SC.POST_BASE_FIELDS + ['media', 'is_banned']
        read_only_fields = [
            'public_id', 'name', 'description', 'is_for_stream'
        ]


class ProfileSerializer(ShortProfileSerializer):
    """Профиль для обычного юзера."""
    posts_count = serializers.SerializerMethodField()
    posts = ShortPostSerializer(
        many=True,
        source='visible_posts',
        read_only=True
    )

    class Meta(ShortProfileSerializer.Meta):
        fields = ShortProfileSerializer.Meta.fields + [
            'posts_count', 'posts', 'created_at', 'updated_at'
        ]

    @swg.extend_schema_field({
        'type': 'integer',
        'example': cs.PostConstants.ONE_POST,
    })
    def get_posts_count(self, obj):
        return obj.posts_count


class ModerationProfileSerializer(ProfileSerializer):
    """Профиль юзера для модерации и стримера."""
    role = serializers.ChoiceField(
        choices=UserRole.choices,
        error_messages={
            'invalid_choice': f'Допустимые роли: {UserRole.values}'
        }
    )

    class Meta(ProfileSerializer.Meta):
        fields = ProfileSerializer.Meta.fields + ['is_banned', 'role']
        read_only_fields = ['username', 'twitch_avatar', 'custom_avatar']

    def update(self, instance, validated_data):
        user = self.context['request'].user

        role = validated_data.get('role')
        is_banned = validated_data.get('is_banned')

        changes = {}
        try:
            CUV.user_cannot_change_himself(user, self.instance)
            CUV.can_user_change_other_user(user, self.instance)

            if role is not None:
                CUV.can_user_change_role(user, self.instance)
                CUV.only_one_streamer(user, role, self.instance)
                changes['role'] = (instance.role, role)

            if is_banned is not None:
                changes['is_banned'] = (instance.is_banned, is_banned)
        except ChangeUserValidationError as e:
            raise serializers.ValidationError(str(e))

        if is_banned is not None:
            Post.objects.filter(user=instance).update(is_banned=is_banned)
            Video.objects.filter(user=instance).update(is_banned=is_banned)

        new_user = super().update(instance, validated_data)

        logger.info(
            'Юзер %s (%s) измененил юзера %s (%s): %s',
            user.username,
            user.role,
            instance.username,
            instance.role,
            changes
        )

        return new_user


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
        user = self.context['request'].user

        post = validated_data['post']
        reason = validated_data['reason']
        other = validated_data.get('other')

        if not post.user.is_user:
            logger.warning(
                'Юзер %s (%s) попытался зарепортить пост %s автора %s (%s)',
                user.username,
                user.role,
                post.public_id,
                post.user.username,
                post.user.role
            )
            raise serializers.ValidationError(
                cs.ReportConstants.MSG_CANNOT_REPORT_STAFF
            )

        if (
            other is not None and reason != cs.ReportReason.OTHER
            or reason == cs.ReportReason.OTHER and other is None
        ):
            logger.warning(
                'Юзер %s (%s) попытался отправить текстовый репорт без '
                'причины \'other\' на пост %s автора %s (%s)',
                user.username,
                user.role,
                post.public_id,
                post.user.username,
                post.user.role
            )
            raise serializers.ValidationError(
                cs.ReportConstants.MSG_OTHER_WITHOUT_REASON
            )

        report = super().create(validated_data)

        logger.info(
            'Юзер %s (%s) отправил репорт %s на пост %s автора %s (%s)',
            user.username,
            user.role,
            report.public_id,
            post.public_id,
            post.user.username,
            post.user.role
        )

        return report

    def to_representation(self, obj):
        """При создании жалобы юзера прост возвращается сообщение."""
        return {
            'message': cs.ReportConstants.MSG_CREATED.format(
                public_id=obj.post.public_id
            )
        }


class ModerationReportSerializer(mx.BaseSerializerMixin):
    """Сериализатор жалобы для модерации."""
    user = serializers.SerializerMethodField(read_only=True)
    post = serializers.SerializerMethodField(read_only=True)
    moder = serializers.SerializerMethodField(read_only=True)
    status = serializers.ChoiceField(
        choices=cs.ReportStatus.choices,
        error_messages={
            'invalid_choice': f'Допустимые статусы: {cs.ReportStatus.values}'
        }
    )

    class Meta(CreateReportSerializer.Meta):
        fields = CreateReportSerializer.Meta.fields + [
            'public_id', 'status', 'moder', 'created_at', 'updated_at'
        ]
        read_only_fields = CreateReportSerializer.Meta.fields + [
            'public_id', 'moder'
        ]

    def update(self, instance, validated_data):
        user = self.context['request'].user
        status = validated_data.get('status')

        old_status = instance.status

        if status == cs.ReportStatus.APPROVED:
            instance.post.is_banned = True
            instance.post.save(update_fields=['is_banned'])

        elif status == cs.ReportStatus.REJECTED:
            instance.post.is_banned = False
            instance.post.save(update_fields=['is_banned'])

        validated_data['moder'] = user

        instance = super().update(instance, validated_data)

        logger.info(
            'Юзер %s (%s) изменил статус репорта %s c %s на %s '
            'от юзера %s на пост %s автора %s',
            user.username,
            user.role,
            instance.public_id,
            old_status,
            instance.status,
            instance.user.username,
            instance.post.public_id,
            instance.post.user.username
        )

        return instance

    def get_user(self, obj) -> str:
        """Возвращаем юзернейм того, кто кинул репорт."""
        return obj.user.username

    def get_post(self, obj) -> str:
        """Возвращаем public_id поста, который зарепортили."""
        return obj.post.public_id

    def get_moder(self, obj) -> str | None:
        """Возвращаем юзернейм модератора, который рассмотрел репорт."""
        if obj.moder is not None:
            return obj.moder.username

        return None

    def validate_status(self, value):
        """Если репорт рассмотрен, то поменять статус на not_viewed нельзя."""
        user = self.context['request'].user

        report = self.instance

        if value == cs.ReportStatus.NOT_VIEWED:
            logger.warning(
                'Юзер %s (%s) попытался изменить статус репорта %s c %s на %s '
                'от юзера %s на пост %s автора %s',
                user.username,
                user.role,
                report.public_id,
                self.instance.status,
                value,
                report.user.username,
                report.post.public_id,
                report.post.user.username
            )
            raise serializers.ValidationError(
                cs.ReportConstants.MSG_STATUS_TO_NOT_VIEWED
            )

        return value


class VideoSerializer(mx.BaseSerializerMixin):
    """Сериализатор видео."""
    youtube_url = serializers.URLField(write_only=True)
    comment = serializers.CharField(
        max_length=VideoConstants.COMMENT_MAX_LENGTH,
        required=False,
        allow_blank=False,
    )
    user = ShortProfileSerializer(read_only=True)
    votings_count = serializers.IntegerField(read_only=True)
    is_voted = serializers.SerializerMethodField()
    category = serializers.ChoiceField(
        choices=Category.choices,
        error_messages={'invalid_choice': CategoryConstants.MSG_ERROR}
    )

    class Meta:
        model = Video
        fields = SC.VIDEO_BASE_FIELDS + ['youtube_url']
        read_only_fields = [
            'public_id', 'youtube_id', 'title', 'preview_url', 'channel_name',
            'pub_date', 'duration', 'views_count', 'likes_count',
            'comments_count'
        ]

    def get_fields(self):
        fields = super().get_fields()

        if self.context['request'].method != 'POST':
            fields.pop('youtube_url')

        return fields

    def create(self, validated_data):
        user = self.context['request'].user

        try:
            video = VideoSerivce.video_uploading(
                url=validated_data['youtube_url'],
                user=user,
                category=validated_data.get('category', ''),
                comment=validated_data.get('comment', '')
            )
        except (
            er.VideoAlreadyExistsError,
            er.VideoIdIncorrectError,
            er.VideoRequestError
        ) as e:
            raise serializers.ValidationError(str(e))

        video.votings_count = VideoConstants.NO_VOTINGS
        video.is_voted = False

        return video

    def update(self, instance, validated_data):
        user = self.context['request'].user

        category = validated_data.get('category')
        comment = validated_data.get('comment')

        changes = {}

        if category is not None:
            changes['category'] = (instance.category, category)

        if comment is not None:
            changes['comment'] = (instance.comment, comment)

        if user.is_user and instance.is_banned:
            logger.warning(
                'Юзер %s (%s) попытался изменить забаненное видео %s',
                user.username,
                user.role,
                instance.public_id
            )
            raise serializers.ValidationError(
                VideoConstants.MSG_CANNOT_CHANGE_BANNED
            )

        video = super().update(instance, validated_data)

        logger.info(
            'Юзер %s (%s) обновил видео %s: %s',
            user.username,
            user.role,
            video.public_id,
            changes
        )

        return video

    @swg.extend_schema_field({
        'type': 'boolean',
        'example': False,
    })
    def get_is_voted(self, obj):
        return obj.is_voted


class ModerationVideoSerializer(
    mx.UpdateBanSerializerMixin, mx.BaseSerializerMixin
):
    """Сериализатор видео для модерации."""
    user = ShortProfileSerializer(read_only=True)
    votings_count = serializers.IntegerField(read_only=True)
    is_voted = serializers.BooleanField(read_only=True)

    class Meta(VideoSerializer.Meta):
        fields = SC.VIDEO_BASE_FIELDS + ['is_banned']
        read_only_fields = VideoSerializer.Meta.read_only_fields + [
            'category', 'comment'
        ]
