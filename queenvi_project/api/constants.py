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
