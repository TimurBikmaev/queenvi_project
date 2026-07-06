import os

from django.utils.text import slugify

from core.constants import EXTENSION_OF_FILE


def avatar_upload_to(instance, filename):
    """Преобразование названия аватарки под юзернейм пользователя."""
    ext = filename.split('.')[EXTENSION_OF_FILE]
    username = slugify(instance.username)
    new_filename = f"{username}.{ext}"
    return os.path.join('avatars', new_filename)
