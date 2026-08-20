from django.db.models import TextChoices


class PostConstants:
    DESCRIPTION_MAX_LENGTH = 1000
    DESCRIPTION_PROFILE_MAX_LENGTH = 40
    MEDIA_MAX_COUNT = 10
    MEDIA_MIN_COUNT = 1
    NAME_MAX_LENGTH = 100
    NAME_PROFILE_MAX_LENGTH = 40
    NO_COMMENTS = 0
    NO_LIKES = 0
    ONE_POST = 1


class CommentConstansts:
    TEXT_MAX_LENGTH = 700


class ReportStatus(TextChoices):
    NOT_VIEWED = 'not_viewed', 'Не рассмотрена'
    APPROVED = 'approved', 'Одобрена'
    REJECTED = 'rejected', 'Отменена'


class ReportReason(TextChoices):
    ADULT = 'adult', 'Контент 18+'
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
    MSG_OTHER_WITHOUT_REASON = (
        'Чтобы отправить текстовую жалобу нужно выбрать причину \'другое\' '
        'и отправить текст жалобы в поле \'other\' :)'
    )
    MSG_STATUS_TO_NOT_VIEWED = (
        'Если репорт рассмотрен, то его нельзя снова сделать нерассмотренным!'
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
    FORMAT_PHOTO = ['.jpg', '.jpeg', '.png']
    FORMAT_VIDEO = ['.mp4']
    PREVIEW_ORDER = 0
    TYPE_MAX_LENGTH = 20


class FilterConstants:
    DAYS_IN_MONTH = 30
    DAYS_IN_WEEK = 7
    DAYS_IN_YEAR = 365
    START_DAY_HOUR = 0
    START_DAY_MINUTE = 0
    START_DAY_SECOND = 0
    START_DAY_MICROSECOND = 0
