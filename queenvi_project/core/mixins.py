from django.db import models
from uuid import uuid4

from core.constants import BaseStatus, PublicIdConstants, StatusConstants


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
        max_length=StatusConstants.MAX_LENGTH,
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


def generate_public_id():
    return uuid4().hex[:PublicIdConstants.MAX_LENGTH]


class PublicIdMixin(models.Model):
    public_id = models.CharField(
        max_length=PublicIdConstants.MAX_LENGTH,
        unique=True,
        default=generate_public_id,
        editable=False
    )

    class Meta:
        abstract = True
