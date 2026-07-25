from pathlib import Path

from django.utils.text import slugify


def avatar_upload_to(instance, filename):
    """Преобразование названия аватарки под юзернейм пользователя."""
    ext = Path(filename).suffix
    username = slugify(instance.username)
    return f'avatars/{username}{ext}'
