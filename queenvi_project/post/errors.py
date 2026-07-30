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
    def __init__(self, staff=False, banned=False, the_same_obj=False):
        msg = 'Нельзя пожаловаться на себя o_O'
        if staff:
            msg = 'Модеру и стримеру нет смысла репортить ^-^'
        elif banned:
            msg = 'Нельзя зарепортить забаненный пост!'
        elif the_same_obj:
            msg = 'Нельзя дважды пожаловаться на один и тот же пост :/'
        super().__init__(msg)
