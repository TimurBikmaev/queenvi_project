from youtube_suggestion.constants import VideoServiceConstants as VSC


class VideoAlreadyExistsError(Exception):
    def __init__(self, is_banned=None):
        message = 'Это видео уже опубликовано в предложке:)'
        if is_banned is True:
            message = (
                'Это видео уже предлагали, но его уже посмотрели на стриме '
                'или модерация отклонила его :('
            )
        super().__init__(message)


class VideoIdIncorrectError(Exception):
    def __init__(self):
        message = (
            'В предложку можно скинуть видео только из YouTube. Ссылка на '
            f'видео должна начинаться с \'{VSC.URL_VIDEO_YOUTUBE_1}\' '
            f'или \'{VSC.URL_VIDEO_YOUTUBE_2}\' и быть доступной ^-^'
        )
        super().__init__(message)


class VideoRequestError(Exception):
    def __init__(self):
        message = 'Не удалось получить данные видео :('
        super().__init__(message)
