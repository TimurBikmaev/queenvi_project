from django.contrib.auth.models import AbstractUser
from django.db import models

from core.mixins import CreatedAtMixin, UpdatedMixin
from user.constants import UserConstants, UserRole
from user.utils import avatar_upload_to


class User(CreatedAtMixin, UpdatedMixin, AbstractUser):
    twitch_id = models.CharField(
        'ID twitch-аккаунта',
        max_length=UserConstants.TWITCH_ID_MAX_LENGTH,
        unique=True,
    )
    twitch_avatar = models.URLField(
        'Твич аватарка',
        null=True,
        blank=True
    )
    custom_avatar = models.ImageField(
        'Кастомная аватарка',
        upload_to=avatar_upload_to,
        null=True,
        blank=True
    )
    role = models.CharField(
        'Роль',
        max_length=UserConstants.ROLE_MAX_LENGTH,
        choices=UserRole.choices,
        default=UserRole.USER,
    )
    is_banned = models.BooleanField('Бан', default=False)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def ban(self):
        self.is_banned = True
        return self

    def unban(self):
        self.is_banned = False
        return self

    def make_user(self):
        self.role = UserRole.USER
        return self

    def make_moder(self):
        self.role = UserRole.moder
        return self

    @property
    def is_user(self):
        return self.role == UserRole.USER

    @property
    def is_moder(self):
        return self.role == UserRole.MODER

    @property
    def is_streamer(self):
        return self.role == UserRole.STREAMER

    def __str__(self):
        return f'{self.username} | {self.role} '
