from django.db import models

from core.constants import PublicIdConstants
from core.utils import generate_public_id


class CreatedAtMixin(models.Model):
    created_at = models.DateTimeField('Дата появления', auto_now_add=True)

    class Meta:
        abstract = True


class UpdatedMixin(models.Model):
    updated_at = models.DateTimeField('Дата изменения', auto_now=True)

    class Meta:
        abstract = True


class PublicIdMixin(models.Model):
    public_id = models.CharField(
        max_length=PublicIdConstants.MAX_LENGTH,
        unique=True,
        default=generate_public_id,
        editable=False
    )

    class Meta:
        abstract = True
