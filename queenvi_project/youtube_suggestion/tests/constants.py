from user.constants import UserRole


class TestVoteConstants:
    NO_VOTES = 0
    ONE_VOTE = 1


class TestVideoConstants:
    COUNT_COMMENTS = 100
    COUNT_LIKES = 100
    COUNT_VIEWS = 100
    DELTA_DAYS_TWO = 2
    DURATION = 90
    FIRST_VIDEO_IDX = 0
    INVALID_NAME = 1
    NO_COMMENTS = 0
    NO_VOTES = 0
    NO_VIDEOS = 0
    ONE_COMMENT = 1
    ONE_LIKE = 1
    ONE_VIDEO = 1
    SECOND_VIDEO_IDX = 1
    TWO_VIDEOS = 2


class MessageConstants:
    IS_VOTED_ANONYMOUS = (
        'Значение поля "is_voted" для анонима при GET-запросах '
        'всегда должно быть False'
    )
    IS_VOTED_TRUE = 'Значение поля "is_voted" False, хотя юзер лайкнул пост'
    IS_VOTED_FALSE = 'Значение поля "is_voted" True, хотя юзер не лайкал пост'
