from pathlib import Path

from post.constants import MediaConstants as MC


class MediaFormatValidationError(Exception):
    def __init__(self, ext, filename):
        filename = Path(filename).name
        super().__init__(
            f'Формат \'{ext}\' файла \'{filename}\' запрещен для загрузки:( '
            f'Допустимые форматы фото: {MC.FORMAT_PHOTO}; '
            f'видео: {MC.FORMAT_VIDEO}; аудио: {MC.FORMAT_AUDIO}'
        )


class UserCanReportError(Exception):
    def __init__(self, the_same_post):
        msg = 'Автор поста не может пожаловаться на свой же пост o_O'
        if the_same_post:
            msg = 'Нельзя дважды пожаловаться на один и тот же пост :/'
        super().__init__(msg)
