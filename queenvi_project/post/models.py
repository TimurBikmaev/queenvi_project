from django.db import models

from core.mixins import TimeStampedMixin
from post.constants import (
    CommentConstansts,
    CommentStatus,
    PostConstants,
    PostStatus,
    ReportConstants,
    ReportStatus
)
from user.models import User


class Post(TimeStampedMixin, models.Model):
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
    status = models.CharField(
        'Статус',
        max_length=PostConstants.STATUS_MAX_LENGTH,
        choices=PostStatus.choices,
        default=PostStatus.VISIBLE,
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор'
    )

    class Meta:
        verbose_name = "Пост"
        verbose_name_plural = "Посты"

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
        constraints = [
            models.UniqueConstraint(
                fields=['post', 'user'],
                name='unique_user_post_like'
            )
        ]
        verbose_name = "Лайк"
        verbose_name_plural = "Лайки"

    def __str__(self):
        return (f'Like id: {self.id} | post_id: {self.post_id}')


class Comment(TimeStampedMixin, models.Model):
    text = models.TextField(
        'Текст',
        max_length=CommentConstansts.TEXT_MAX_LENGTH
    )
    status = models.CharField(
        'Статус',
        max_length=PostConstants.STATUS_MAX_LENGTH,
        choices=CommentStatus.choices,
        default=CommentStatus.VISIBLE,
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

    def __str__(self):
        return (f'Comment id: {self.id} | post_id: {self.post_id}')


class Report(models.Model):
    reason = models.TextField(
        max_length=ReportConstants.REASON_MAX_LENGTH,
        min_length=ReportConstants.REASON_MIN_LENGTH
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name='Жалобы'
    )
    status = models.CharField(
        'Статус',
        max_length=ReportConstants.STATUS_MAX_LENGTH,
        choices=ReportStatus.choices,
        default=ReportStatus.NOT_VIEWED,
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reported_posts',
        verbose_name='Жалобы'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['post', 'user'],
                name='unique_user_post_report'
            )
        ]
        verbose_name = "Жалоба"
        verbose_name_plural = "Жалобы"

    def __str__(self):
        return (f'Report id: {self.id} | post_id: {self.post_id}')
