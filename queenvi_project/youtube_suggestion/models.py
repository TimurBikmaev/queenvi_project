from django.contrib.auth import get_user_model
from django.db import models

from core.mixins import CreatedAtMixin, PublicIdMixin, UpdatedMixin
from youtube_suggestion.constants import (
    Category, CategoryConstants,  VideoConstants
)


User = get_user_model()


class Video(CreatedAtMixin, UpdatedMixin, PublicIdMixin):
    youtube_id = models.CharField(
        'YouTube ID',
        max_length=VideoConstants.VIDEO_ID_MAX_LENGTH,
        unique=True
    )
    title = models.CharField(
        'Название',
        max_length=VideoConstants.NAME_MAX_LENGTH
    )
    preview_url = models.URLField('Превью')
    channel_name = models.CharField(
        'Канал',
        max_length=VideoConstants.CHANNEL_NAME_MAX_LENGTH
    )
    pub_date = models.DateTimeField('Опубликовано на YouTube')
    duration = models.SmallIntegerField('Длительность в секундах')
    views_count = models.PositiveBigIntegerField('Просмотры')
    likes_count = models.PositiveIntegerField('Лайки')
    comments_count = models.PositiveIntegerField('Коммы из Youtube')
    is_banned = models.BooleanField('Бан', default=False)
    category = models.CharField(
        'Категория',
        max_length=CategoryConstants.CATEGORY_MAX_LENGTH,
        choices=Category.choices,
        blank=False
    )
    comment = models.CharField(
        'Комментарий автора',
        max_length=VideoConstants.COMMENT_MAX_LENGTH,
        blank=True
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='videos',
        verbose_name='Автор'
    )

    class Meta:
        verbose_name = 'Видео'
        verbose_name_plural = 'Видео'
        indexes = [
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return f'Видео {self.public_id} | {self.user.username}'


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
