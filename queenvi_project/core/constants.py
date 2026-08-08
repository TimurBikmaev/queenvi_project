class LoggingConstants:
    BACKUP_COUNT = 5
    CONFIG_VERSION = 1
    FILE_MAX_SIZE = 10 * 1024 * 1024


class PublicIdConstants:
    MAX_LENGTH = 8
    URL_REGEX = rf'[a-zA-Z0-9]{{{MAX_LENGTH}}}'


class AdminConstants:
    NO_EXTRA = 0
