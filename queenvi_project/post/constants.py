from django.db.models import TextChoices


class PostConstants:
    DESCRIPTION_MAX_LENGTH = 1000
    NAME_MAX_LENGTH = 100


class CommentConstansts:
    TEXT_MAX_LENGTH = 700


class ReportStatus(TextChoices):
    NOT_VIEWED = 'not_viewed', 'Не рассмотрена'
    APPROVED = 'approved', 'Одобрена'
    REJECTED = 'rejected', 'Отменена'


class ReportReasonStatus(TextChoices):
    ADULT = 'adult', 'Контент для взрослых [18+]'
    ILLEGAL = 'illegal', 'Незаконный'
    ADVERTISING = 'advertising', 'Реклама'
    SPAM = 'spam', 'Спам'
    OTHER = 'other', 'Другое'


class ReportConstants:
    MSG_CANNOT_REPORT_STAFF = (
        'Нельзя пожаловаться на пост модера или стримера -_-'
    )
    MSG_CREATED = (
        'Жалоба на пост {public_id} отправлена! Модерация ее проверит и при '
        'обнаружении нарушения примет меры. Спасибо, что делаешь сообщество '
        'дружелюбнее :)'
    )
    MSG_STATUS_TO_NOT_VIEWED = (
        'Если репорт рассмотрен, то его нельзя определить нерассмотренным!'
    )
    OTHER_MAX_LENGTH = 700
    REASON_MAX_LENGTH = 20
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
