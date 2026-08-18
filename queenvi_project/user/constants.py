from django.db.models import TextChoices


class UserRole(TextChoices):
    USER = 'user', 'Юзер'
    MODER = 'moder', 'Модер'
    STREAMER = 'streamer', 'Стример'


class UserConstants:
    AVATAR_MAX_HEIGHT = 4000
    AVATAR_MAX_SIZE = 1 * 1024 * 1024
    AVATAR_MAX_SIZE_MB = 1
    AVATAR_MAX_WIDTH = 4000
    AVATAR_UUID_LEN = 8
    ROLE_MAX_LENGTH = 20
    TWITCH_ID_MAX_LENGTH = 35

    MSG_ONLY_STAFF = 'Обычным юзерам доступ запрещен.'
    MSG_BANNED_USER = 'Забаненным пользователям доступ запрещен.'
    MSG_ANON_AND_BANNED = f'Анонимам доступ запрещен. | {MSG_BANNED_USER}'
    MSG_404 = 'Объект не найден.'
    MSG_BAN_404_OBJ = (
        'Обычные пользователи не могут смотреть забаненные объекты. | '
        f'{MSG_404}'
    )
    MSG_NOT_AUTHOR = 'Только автор может изменять объект.'

    MSG_SIZE = f'Максимально допустимый размер файла {AVATAR_MAX_SIZE_MB} МБ.'
    MSG_RESOLUTION = (
        f'Максимально допустимое разрешение: '
        f'{AVATAR_MAX_WIDTH}x{AVATAR_MAX_HEIGHT}.'
    )


class TwitchLoginConstants:
    IDX_USER_DATA = 0
    LENGTH_STATE = 32
    SCOPE = 'user:read:email'
    TIME_FOR_ANSWER = 10
    TYPE_GRAND = 'authorization_code'
    TYPE_RESPONSE = 'code'
    URL_AUTH = 'https://id.twitch.tv/oauth2/authorize?'
    URL_USER_INFO = 'https://api.twitch.tv/helix/users'
    URL_TOKEN = 'https://id.twitch.tv/oauth2/token'
