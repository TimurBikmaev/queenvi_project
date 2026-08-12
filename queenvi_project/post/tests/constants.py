from user.constants import UserRole


class ListPostConstants:
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
    SECOND_POST_IDX = 1
    TWO_POSTS = 2


class ImageConstants:
    CONTENT_TYPE = 'image/jpeg'
    FIRST_MEDIA_IDX = 0
    FORMAT = 'JPEG'
    RESOLUTION = (1920, 1080)
    READ_FILE_FROM_BEGIN = 0
