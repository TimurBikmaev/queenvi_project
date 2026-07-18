from django.db.models import TextChoices


EXTENSION_OF_FILE = -1
PUBLIC_ID_MAX_LENGTH = 12
STATUS_MAX_LENGTH = 20


class BaseStatus(TextChoices):
    VISIBLE = 'visible', 'Виден всем'
    HIDDEN = 'hidden', 'Спрятан от всех и ждет модерации'
    BANNED = 'banned', 'Заблокирован модератором'


class TwitchLoginConstants:
    IDX_USER_DATA = 0
    LENGTH_STATE = 32
    SCOPE = 'user:read:email'
    TIME_FOR_ANSWER = 10
    TYPE_GRAND = "authorization_code"
    TYPE_RESPONSE = 'code'
    URL_AUTH = "https://id.twitch.tv/oauth2/authorize?"
    URL_USER_INFO = "https://api.twitch.tv/helix/users"
    URL_TOKEN = "https://id.twitch.tv/oauth2/token"
