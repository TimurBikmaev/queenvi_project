from django.db.models import TextChoices


class BaseStatus(TextChoices):
    VISIBLE = 'visible', 'Виден всем'
    HIDDEN = 'hidden', 'Спрятан от всех и ждет модерации'
    BANNED = 'banned', 'Заблокирован модератором'


class PostStatus(BaseStatus):
    pass


class CommentStatus(BaseStatus):
    pass


class ReportStatus(TextChoices):
    NOT_VIEWED = 'not_viewed', 'Не рассмотрена'
    APPROVED = 'approved', 'Одобрена'
    REJECTED = 'rejected', 'Отменена'


class CommentConstansts:
    TEXT_MAX_LENGTH = 700


class PostConstants:
    NAME_MAX_LENGTH = 100
    DESCRIPTION_MAX_LENGTH = 1000
    STATUS_MAX_LENGTH = 20


class ReportConstants:
    REASON_MAX_LENGTH = 700
    REASON_MIN_LENGTH = 100
    STATUS_MAX_LENGTH = 20
