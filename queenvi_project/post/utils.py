import logging
from pathlib import Path
from shutil import rmtree

from django.conf import settings
from django.utils import timezone

from post.constants import MediaConstants as MC, MediaType
from post.errors import MediaFormatValidationError


logger = logging.getLogger(__name__)


class FilterUtils:
    def post_queryset(queryset, now, days):
        """Возвращает queryset с фильтром по дате создания поста."""
        return queryset.filter(
            created_at__gte=now - timezone.timedelta(days=days)
        )


class MediaUtils:
    def media_upload_to(instance, filename):
        """Переименование файлов и создание медиа-каталогов постов."""
        ext = Path(filename).suffix
        filename = f'{instance.order}_{instance.file_type}'
        return f'posts/{instance.post.public_id}/{filename}{ext}'

    def del_media_catalog(public_id):
        """Удаление медиа-каталога поста с файлами."""
        post_dir = Path(settings.MEDIA_ROOT)/'posts'/public_id
        if post_dir.exists():
            rmtree(post_dir)
            logger.info(
                'Каталог медиа у поста %s был успешно удален',
                public_id
            )

    def file_type_revealing(file):
        """Определение формата файла из допустимых."""
        extension = Path(file.name).suffix.lower()
        file_type = None
        if extension in MC.FORMAT_PHOTO:
            file_type = MediaType.PHOTO
        elif extension in MC.FORMAT_VIDEO:
            file_type = MediaType.VIDEO
        elif extension in MC.FORMAT_AUDIO:
            file_type = MediaType.AUDIO
        return file_type, extension

    def collect_media_data(files):
        """Определение и проверка медиа при создании и обновлении поста."""
        media_data = []
        for idx, file in enumerate(files):
            file_type, ext = MediaUtils.file_type_revealing(file)
            if file_type is None:
                logger.warning(
                    'Файл %s не соответствует допустимому формату',
                    file.name
                )
                raise MediaFormatValidationError(ext, file.name)
            media_data.append({
                'file': file,
                'file_type': file_type,
                'order': idx
            })
        return media_data
