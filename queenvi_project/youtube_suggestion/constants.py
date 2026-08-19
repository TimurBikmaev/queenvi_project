from django.db.models import TextChoices


class VideoConstants:
    CHANNEL_NAME_MAX_LENGTH = 100
    COMMENT_MAX_LENGTH = 50
    MSG_CANNOT_CHANGE_BANNED = 'Нельзя изменить забаненное видео :('
    NAME_MAX_LENGTH = 100
    NO_VOTINGS = 0
    VIDEO_ID_MAX_LENGTH = 11


class Category(TextChoices):
    HUMUROUS = 'humurous', 'Смешные'
    TRUECRIME = 'truecrime', 'Трукрайм'
    COGNITIVE = 'cognitive', 'Познавательные'
    TRAILERS = 'trailers', 'Трейлеры'
    DIFFERENT = 'different', 'Разное'


class CategoryConstants:
    CATEGORY_MAX_LENGTH = 20
    MSG_ERROR = f'Допустимые категории: {Category.values}'


class VideoServiceConstants:
    FORMAT_DURATION = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
    IDX_VIDEO_DATA = 0
    NO_TIME = 0
    PART = 'snippet,statistics,contentDetails'
    RESOLUTIONS = 'maxres', 'standard', 'high', 'medium', 'default'
    SEC_FROM_HOURS = 3600
    SEC_FROM_MINUTS = 60
    URL_GET_VIDEO_DATA = 'https://www.googleapis.com/youtube/v3/videos'
    URL_VIDEO_YOUTUBE_1 = 'https://www.youtube.com/watch?v='
    URL_VIDEO_YOUTUBE_2 = 'https://youtu.be/'
