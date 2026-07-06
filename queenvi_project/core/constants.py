from django.db.models import TextChoices


EXTENSION_OF_FILE = -1


class BaseStatus(TextChoices):
    VISIBLE = 'visible', 'Виден всем'
    HIDDEN = 'hidden', 'Спрятан от всех и ждет модерации'
    BANNED = 'banned', 'Заблокирован модератором'


class StatusConstants:
    STATUS_MAX_LENGTH = 20
