from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from core.mixins import CreatedAtMixin, UpdatedMixin
from user.constants import UserConstants
from user.utils import avatar_upload_to


class UserRole(models.TextChoices):
    USER = 'user', 'Пользователь'
    MODERATOR = 'moderator', 'Модератор'
    STREAMER = 'streamer', 'Стример'


class User(CreatedAtMixin, UpdatedMixin, AbstractUser):
    twitch_id = models.CharField(
        'ID twitch-аккаунта',
        max_length=UserConstants.TWITCH_ID_MAX_LENGTH,
        unique=True,
    )
    avatar = models.ImageField(
        'Аватар',
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
    warnings = models.SmallIntegerField(
        'Предупреждения',
        default=UserConstants.NO_WARNINGS,
        validators=[
            MaxValueValidator(UserConstants.WARNINGS_TO_AUTOBAN),
            MinValueValidator(UserConstants.NO_WARNINGS)
        ],
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def check_autoban(self):
        if self.warnings >= UserConstants.WARNINGS_TO_AUTOBAN:
            self.is_active = False
        return self

    def add_warning(self):
        self.warnings = min(
            self.warnings + UserConstants.ONE_WARNING,
            UserConstants.WARNINGS_TO_AUTOBAN
        )
        self.check_autoban()
        return self

    def reset_warnings(self):
        self.warnings = UserConstants.NO_WARNINGS
        self.is_active = True
        return self

    def ban(self):
        self.is_active = False
        return self

    def unban(self):
        self.is_active = True
        return self

    def make_moderator(self):
        self.role = UserRole.MODERATOR
        return self

    @property
    def is_moderator(self):
        return self.role == UserRole.MODERATOR

    @property
    def is_streamer(self):
        return self.role == UserRole.STREAMER

    @property
    def is_banned(self):
        return not self.is_active

    def __str__(self):
        return f'User id: {self.id} | role: {self.role}'
