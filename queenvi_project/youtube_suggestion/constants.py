from django.db.models import TextChoices


class VideoConstants:
    CHANNEL_NAME_MAX_LENGTH = 100
    COMMENT_MAX_LENGTH = 50
    NAME_MAX_LENGTH = 100
    PREVIEW_MAX_LENGTH = 1000
    VIDEO_ID_MAX_LENGTH = 20


class Category(TextChoices):
    HUMUROUS = 'humurous', 'Смешные'
    TRUECRIME = 'truecrime', 'Трукрайм'
    COGNITIVE = 'cognitive', 'Познавательные'
    TRAILERS = 'trailers', 'Трейлеры'
    DIFFERENT = 'different', 'Разное'


class CategoryConstants:
    CATEGORY_MAX_LENGTH = 20
