from django.db import models


class CreatedAtMixin(models.Model):
    created_at = models.DateTimeField('Дата появления', auto_now_add=True)

    class Meta:
        abstract = True


class TimeStampedMixin(CreatedAtMixin):
    updated_at = models.DateTimeField('Дата изменения', auto_now=True)

    class Meta:
        abstract = True
