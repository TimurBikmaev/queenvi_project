from pathlib import Path

from core.utils import generate_public_id


def avatar_upload_to(instance, filename):
    """Преобразование названия аватарки под генерацию uuid."""
    ext = Path(filename).suffix
    return f'avatars/{generate_public_id()}{ext}'
