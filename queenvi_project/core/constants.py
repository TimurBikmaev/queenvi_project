from user.constants import UserRole


class LoggingConstants:
    BACKUP_COUNT = 5
    CONFIG_VERSION = 1
    FILE_MAX_SIZE = 10 * 1024 * 1024


class PublicIdConstants:
    MAX_LENGTH = 8
    URL_REGEX = rf'[a-zA-Z0-9]{{{MAX_LENGTH}}}'


class AdminConstants:
    NO_EXTRA = 0


class TestConstants:
    PARAMS_AUTH_USERS = [UserRole.USER, UserRole.MODER, UserRole.STREAMER]
    PARAMS_BANNED_USERS = [UserRole.USER, UserRole.MODER]
    PARAMS_NOT_STAFF = [None, UserRole.USER]
    PARAMS_STAFF = [UserRole.MODER, UserRole.STREAMER]
    PARAMS_USERS = PARAMS_NOT_STAFF + PARAMS_STAFF
