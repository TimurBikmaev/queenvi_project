from django.contrib.auth import get_user_model
from django.db import models

from core.mixins import CreatedAtMixin, PublicIdMixin, UpdatedMixin
from post.constants import (
    CommentConstansts,
    MediaConstants,
    MediaType,
    PostConstants,
    ReportConstants,
    ReportReason,
    ReportStatus
)
from post.utils import MediaUtils


User = get_user_model()


class Post(PublicIdMixin, CreatedAtMixin, UpdatedMixin):
    name = models.CharField(
        'Название',
        max_length=PostConstants.NAME_MAX_LENGTH
    )
    description = models.CharField(
        'Описание',
        max_length=PostConstants.DESCRIPTION_MAX_LENGTH,
        blank=True
    )
    is_for_stream = models.BooleanField('Для стрима', default=True)
    is_banned = models.BooleanField('Бан', default=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор'
    )

    class Meta:
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'
        indexes = [
            models.Index(fields=['is_banned']),
            models.Index(fields=['created_at']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f'Пост {self.public_id} | {self.user.username}'


class Like(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name='Лайки'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='liked_posts',
        verbose_name='Лайки'
    )

    class Meta:
        verbose_name = 'Лайк'
        verbose_name_plural = 'Лайки'
        constraints = [
            models.UniqueConstraint(
                fields=['post', 'user'],
                name='unique_user_post_like'
            )
        ]
        indexes = [
            models.Index(fields=['post']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return (f'Like id: {self.id} | post_id: {self.post_id}')


class Comment(PublicIdMixin, CreatedAtMixin, UpdatedMixin):
    text = models.TextField(
        'Текст',
        max_length=CommentConstansts.TEXT_MAX_LENGTH
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Пост'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='commented_posts',
        verbose_name='Автор'
    )

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['post']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f'Коммент {self.public_id} | {self.user.username}'


class Report(PublicIdMixin, CreatedAtMixin, UpdatedMixin):
    reason = models.CharField(
        'Причина',
        max_length=ReportConstants.REASON_MAX_LENGTH,
        choices=ReportReason.choices,
    )
    other = models.TextField(
        'Другое',
        max_length=ReportConstants.OTHER_MAX_LENGTH,
        blank=True
    )
    status = models.CharField(
        'Статус',
        max_length=ReportConstants.STATUS_MAX_LENGTH,
        choices=ReportStatus.choices,
        default=ReportStatus.NOT_VIEWED,
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name='Пост'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name='Автор'
    )
    moder = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_reports",
        verbose_name='Модер'
    )

    class Meta:
        verbose_name = 'Репорт'
        verbose_name_plural = 'Репорты'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['post', 'user'],
                name='unique_user_post_report'
            )
        ]
        indexes = [
            models.Index(fields=['status']),
        ]

    def make_approved(self):
        self.status = ReportStatus.APPROVED
        return self

    def make_rejected(self):
        self.status = ReportStatus.REJECTED
        return self

    @property
    def is_not_viewed(self):
        return self.status == ReportStatus.NOT_VIEWED

    @property
    def is_approved(self):
        return self.status == ReportStatus.APPROVED

    @property
    def is_rejected(self):
        return self.status == ReportStatus.REJECTED

    def __str__(self):
        return f'Репорт {self.public_id} | {self.user.username}'


class Media(CreatedAtMixin):
    file = models.FileField('Медиа', upload_to=MediaUtils.media_upload_to)
    file_type = models.CharField(
        'Тип файла',
        max_length=MediaConstants.TYPE_MAX_LENGTH,
        choices=MediaType.choices,
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='media',
        verbose_name='Медиа'
    )
    order = models.PositiveSmallIntegerField()

    class Meta:
        verbose_name = 'Медиа'
        verbose_name_plural = 'Медиа'
