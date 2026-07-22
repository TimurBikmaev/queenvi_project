from pathlib import Path
from http import HTTPStatus

from rest_framework.response import Response

from post.constants import MediaType


def date_to_json(value, status=HTTPStatus.BAD_REQUEST, key='error'):
    return Response({key: value}, status=status)


def file_extension_revealing(file):
    """Определяет формат файла."""
    extension = Path(file.name).suffix.lower()
    if extension in ['.jpg', '.png']:
        type_of_file = MediaType.PHOTO
    elif extension in ['.mp4']:
        type_of_file = MediaType.VIDEO
    elif extension in ['.mp3']:
        type_of_file = MediaType.AUDIO
    return type_of_file
