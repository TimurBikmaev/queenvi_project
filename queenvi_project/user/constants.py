from django.db.models import TextChoices


class UserRole(TextChoices):
    USER = 'user', 'Пользователь'
    MODERATOR = 'moderator', 'Модератор'
    STREAMER = 'streamer', 'Стример'


class UserConstants:
    AVATAR_MAX_HEIGHT = 4000
    AVATAR_MAX_SIZE = 1 * 1024 * 1024
    AVATAR_MAX_WIDTH = 4000
    ROLE_MAX_LENGTH = 20
    TWITCH_ID_MAX_LENGTH = 35


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
