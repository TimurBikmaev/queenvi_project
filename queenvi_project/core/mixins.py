from django.db import models
import shortuuid

from core.constants import BaseStatus, PUBLIC_ID_MAX_LENGTH, STATUS_MAX_LENGTH


class CreatedAtMixin(models.Model):
    created_at = models.DateTimeField('Дата появления', auto_now_add=True)

    class Meta:
        abstract = True


class UpdatedMixin(models.Model):
    updated_at = models.DateTimeField('Дата изменения', auto_now=True)

    class Meta:
        abstract = True


class StatusMixin(models.Model):
    status = models.CharField(
        'Статус',
        max_length=STATUS_MAX_LENGTH,
        choices=BaseStatus.choices,
        default=BaseStatus.VISIBLE,
    )

    def make_visible(self):
        self.status = BaseStatus.VISIBLE
        return self

    def make_hidden(self):
        self.status = BaseStatus.HIDDEN
        return self

    def make_banned(self):
        self.status = BaseStatus.BANNED
        return self

    @property
    def is_visible(self):
        return self.status == BaseStatus.VISIBLE

    @property
    def is_hidden(self):
        return self.status == BaseStatus.HIDDEN

    @property
    def is_banned(self):
        return self.status == BaseStatus.BANNED

    class Meta:
        abstract = True


class PublicIdMixin(models.Model):
    public_id = models.CharField(
        max_length=PUBLIC_ID_MAX_LENGTH,
        unique=True,
        default=lambda: shortuuid.uuid()[
            :PUBLIC_ID_MAX_LENGTH
        ],
        editable=False
    )

    class Meta:
        abstract = True
