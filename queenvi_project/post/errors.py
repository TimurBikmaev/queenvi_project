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
