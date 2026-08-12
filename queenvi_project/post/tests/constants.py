from user.constants import UserRole


class TestPostConstants:
    FIRST_POST_IDX = 0
    NO_COMMENTS = 0
    NO_LIKES = 0
    NO_POSTS = 0
    ONE_COMMENT = 1
    ONE_LIKE = 1
    ONE_POST = 1
    FILTER_PARAMS = [
        (None, True,),
        (None, False,),
        (UserRole.USER, True,),
        (UserRole.USER, False,),
        (UserRole.MODER, True,),
        (UserRole.MODER, False,),
        (UserRole.STREAMER, True,),
        (UserRole.STREAMER, False,),
    ]
    PRIVATE_FIELDS_PARAMS = [
        (None, False),
        (UserRole.USER, False),
        (UserRole.MODER, True),
        (UserRole.STREAMER, True),
    ]
    SECOND_POST_IDX = 1
    TWO_POSTS = 2
    USER_PARAMS = [
        (None),
        (UserRole.USER),
        (UserRole.MODER),
        (UserRole.STREAMER),
    ]


class MessageConstants:
    IS_LIKED_ANONYMOUS = (
        'Значение поля is_liked для анонима при GET-запросах '
        'всегда должно быть False'
    )
    IS_LIKED_TRUE = 'Значение поля is_liked False, хотя юзер лайкнул пост'
    IS_LIKED_FALSE = 'Значение поля is_liked True, хотя юзер не лайкал пост'


class ImageConstants:
    CONTENT_TYPE = 'image/jpeg'
    FIRST_MEDIA_IDX = 0
    FORMAT = 'JPEG'
    ONE_MEDIA = 1
    RESOLUTION = (1920, 1080)
    READ_FILE_FROM_BEGIN = 0
    SECOND_MEDIA_IDX = 1
    THIRD_MEDIA_IDX = 2
    THREE_MEDIA = 3
