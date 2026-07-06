from django.db.models import TextChoices


class PostConstants:
    NAME_MAX_LENGTH = 100
    DESCRIPTION_MAX_LENGTH = 1000


class CommentConstansts:
    TEXT_MAX_LENGTH = 700


class ReportStatus(TextChoices):
    NOT_VIEWED = 'not_viewed', 'Не рассмотрена'
    APPROVED = 'approved', 'Одобрена'
    REJECTED = 'rejected', 'Отменена'


class ReportConstants:
    REASON_MAX_LENGTH = 700
    REASON_MIN_LENGTH = 100
    STATUS_MAX_LENGTH = 20


class MediaType(TextChoices):
    PHOTO = 'photo', 'Фото'
    VIDEO = 'video', 'Видео'
    AUDIO = 'audio', 'Аудио'


class MediaConstants:
    TYPE_MAX_LENGTH = 20
