from django.db import models

from core.mixins import CreatedAtMixin, StatusMixin, UpdatedMixin
from post.constants import (
    CommentConstansts,
    MediaConstants,
    MediaType,
    PostConstants,
    ReportConstants,
    ReportStatus
)
from post.utils import media_upload_to
from user.models import User


class Post(CreatedAtMixin, UpdatedMixin, StatusMixin):
    name = models.CharField(
        'Название',
        max_length=PostConstants.NAME_MAX_LENGTH
    )
    description = models.CharField(
        'Описание',
        max_length=PostConstants.DESCRIPTION_MAX_LENGTH,
        blank=True
    )
    is_for_stream = models.BooleanField('Подходит для стрима', default=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Посты'
    )

    class Meta:
        verbose_name = "Пост"
        verbose_name_plural = "Посты"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["user"]),
        ]

    def __str__(self):
        return (f'Post id: {self.id} | user_id: {self.user_id}')


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
        verbose_name = "Лайк"
        verbose_name_plural = "Лайки"
        constraints = [
            models.UniqueConstraint(
                fields=['post', 'user'],
                name='unique_user_post_like'
            )
        ]
        indexes = [
            models.Index(fields=["post"]),
            models.Index(fields=["user"]),
        ]

    def __str__(self):
        return (f'Like id: {self.id} | post_id: {self.post_id}')


class Comment(CreatedAtMixin, UpdatedMixin, StatusMixin):
    text = models.TextField(
        'Текст',
        max_length=CommentConstansts.TEXT_MAX_LENGTH
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Комментарии'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='commented_posts',
        verbose_name='Комментарии'
    )

    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"
        indexes = [
            models.Index(fields=["post"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return (f'Comment id: {self.id} | post_id: {self.post_id}')


class Report(models.Model):
    reason = models.TextField(
        'Причина',
        max_length=ReportConstants.REASON_MAX_LENGTH,
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
        verbose_name='Жалобы'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reported_posts',
        verbose_name='Жалобы'
    )

    class Meta:
        verbose_name = "Жалоба"
        verbose_name_plural = "Жалобы"
        constraints = [
            models.UniqueConstraint(
                fields=['post', 'user'],
                name='unique_user_post_report'
            )
        ]
        indexes = [
            models.Index(fields=["status"]),
        ]

    def make_not_viewed(self):
        self.status = ReportStatus.NOT_VIEWED
        return self

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
        return (f'Report id: {self.id} | post_id: {self.post_id}')


class Media(CreatedAtMixin):
    file = models.FileField('Медиа', upload_to=media_upload_to)
    type_of_file = models.CharField(
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

    class Meta:
        verbose_name = "Медиа"
        verbose_name_plural = "Медиа"
