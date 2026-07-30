from django.db import models

from core.mixins import CreatedAtMixin, PublicIdMixin, UpdatedMixin
from user.models import User
from youtube_suggestion.constants import (
    Category, CategoryConstants,  VideoConstants
)


class Video(CreatedAtMixin, UpdatedMixin, PublicIdMixin):
    youtube_id = models.CharField(
        'ID видео',
        max_length=VideoConstants.VIDEO_ID_MAX_LENGTH,
        unique=True
    )
    title = models.CharField(
        'Название',
        max_length=VideoConstants.NAME_MAX_LENGTH
    )
    preview_url = models.URLField('Превью')
    channel_name = models.CharField(
        'Название канала',
        max_length=VideoConstants.CHANNEL_NAME_MAX_LENGTH
    )
    pub_date = models.DateTimeField('Дата публикации')
    duration = models.SmallIntegerField('Длительность')
    views_count = models.PositiveBigIntegerField('Число просмотров')
    likes_count = models.PositiveIntegerField('Число лайков')
    comments_count = models.PositiveIntegerField('Число комментариев')
    is_banned = models.BooleanField('Забанено ли', default=False)
    category = models.CharField(
        'Категория',
        max_length=CategoryConstants.CATEGORY_MAX_LENGTH,
        choices=Category.choices,
        blank=True
    )
    comment = models.CharField(
        'Комментарий к видео',
        max_length=VideoConstants.COMMENT_MAX_LENGTH,
        blank=True
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='videos',
        verbose_name='Видео'
    )

    class Meta:
        verbose_name = 'Видео'
        verbose_name_plural = 'Видео'
        indexes = [
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return (f'Video id: {self.id} | user_id: {self.user_id}')


class Voting(models.Model):
    video = models.ForeignKey(
        Video,
        on_delete=models.CASCADE,
        related_name='votes',
        verbose_name='Голоса'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='voted_videos',
        verbose_name='Голоса'
    )

    class Meta:
        verbose_name = 'Голос'
        verbose_name_plural = 'Голоса'
        constraints = [
            models.UniqueConstraint(
                fields=['video', 'user'],
                name='unique_user_video_voting'
            )
        ]
        indexes = [
            models.Index(fields=['video']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return (f'Voting id: {self.id} | video_id: {self.video_id}')
