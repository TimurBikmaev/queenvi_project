import os
import uuid

from core.constants import EXTENSION_OF_FILE


def media_upload_to(instance, filename):
    """Преобразование названия медиа под id поста и uuid."""
    ext = filename.split('.')[EXTENSION_OF_FILE]
    new_filename = f"{instance.post_id}/{uuid.uuid4()}.{ext}"
    return os.path.join('media/', new_filename)
