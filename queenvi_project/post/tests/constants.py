

class TestLikeConstants:
    NO_LIKES = 0
    ONE_LIKE = 1


class TestPostConstants:
    DELTA_TWO_DAYS = 2
    FIRST_POST_IDX = 0
    INVALID_NAME = 1
    NO_COMMENTS = 0
    NO_LIKES = 0
    NO_POSTS = 0
    ONE_COMMENT = 1
    ONE_LIKE = 1
    ONE_POST = 1
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
    EXTENSION_IDX = -1
    FIRST_MEDIA_IDX = 0
    FORMAT = 'JPEG'
    ONE_MEDIA = 1
    READ_FILE_FROM_BEGIN = 0
    SECOND_MEDIA_IDX = 1
    THIRD_MEDIA_IDX = 2


class TestReportConstants:
    DELTA_TWO_DAYS = 2
    FIRST_REPORT_IDX = 0
    ONE_REPORT = 1
    SECOND_REPORT_IDX = 1
    TWO_REPORTS = 2


class TestCommentConstants:
    DELTA_TWO_DAYS = 2
    FIRST_COMMENT_IDX = 0
    ONE_COMMENT = 1
    SECOND_COMMENT_IDX = 1
    TWO_COMMENTS = 2
