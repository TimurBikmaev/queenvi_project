from user.constants import UserRole


class TestPostConstants:
    FIRST_POST_IDX = 0
    INVALID_NAME = 1
    NO_COMMENTS = 0
    NO_LIKES = 0
    NO_POSTS = 0
    ONE_COMMENT = 1
    ONE_LIKE = 1
    ONE_POST = 1
    PARAMS_FILTER = [
        (None, True,),
        (None, False,),
        (UserRole.USER, True,),
        (UserRole.USER, False,),
        (UserRole.MODER, True,),
        (UserRole.MODER, False,),
        (UserRole.STREAMER, True,),
        (UserRole.STREAMER, False,),
    ]
    PARAMS_AUTH_USER = [
        (UserRole.USER),
        (UserRole.MODER),
        (UserRole.STREAMER),
    ]
    PARAMS_STAFF = [
        (UserRole.MODER),
        (UserRole.STREAMER)
    ]
    PARAMS_USER = [(None)] + PARAMS_AUTH_USER
    SECOND_POST_IDX = 1
    TWO_POSTS = 2


class MessageConstants:
    IS_LIKED_ANONYMOUS = (
        'Значение поля is_liked для анонима при GET-запросах '
        'всегда должно быть False'
    )
    IS_LIKED_TRUE = 'Значение поля is_liked False, хотя юзер лайкнул пост'
    IS_LIKED_FALSE = 'Значение поля is_liked True, хотя юзер не лайкал пост'


class TestMediaConstants:
    CONTENT_TYPE = 'image/jpeg'
    FIRST_MEDIA_IDX = 0
    FORMAT = 'JPEG'
    FROM_SECOND_MEDIA = 1
    FROM_THIRD_MEDIA = 2
    ONE_MEDIA = 1
    RESOLUTION = (1920, 1080)
    READ_FILE_FROM_BEGIN = 0
    SECOND_MEDIA_IDX = 1
    STEP = -1
    THIRD_MEDIA_IDX = 2
    THREE_MEDIA = 3
    TO_FIRST_MEDIA = -1
    TWO_MEDIA = 2
