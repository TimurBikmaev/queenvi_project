from django.db.models import TextChoices


class PostCommentStatus(TextChoices):
    VISIBLE = 'visible', 'Виден всем'
    HIDDEN = 'hidden', 'Спрятан от всех и ждет модерации'
    BANNED = 'banned', 'Заблокирован модератором'


class PostCommentStatusConstants:
    MAX_LENGTH = 20


class PostConstants:
    DESCRIPTION_MAX_LENGTH = 1000
    NAME_MAX_LENGTH = 100


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
    FORMAT_AUDIO = ['.mp3']
    FORMAT_PHOTO = ['.jpg', '.jpeg', '.jfif', '.png']
    FORMAT_VIDEO = ['.mp4']
    PREVIEW_ORDER = 0
    TYPE_MAX_LENGTH = 20
