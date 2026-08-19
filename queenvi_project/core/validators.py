import logging

from core.errors import ChangeObjValidationError


logger = logging.getLogger(__name__)


class ChangeBanStatusValidator:
    def cannot_unban_obj_of_banned_user(obj, user):
        """Нельзя разбанить объект забаненного пользователя."""
        if obj.user.is_banned is True and obj.is_banned is True:
            logger.warning(
                'Юзер %s (%s) попытался разбанить объект %s '
                'забаненного юзера %s (%s), is_banned=%s',
                user.username,
                user.role,
                obj.public_id,
                obj.user.username,
                obj.user.role,
                obj.user.is_banned
            )
            raise ChangeObjValidationError()

    def cannot_change_streamer_obj(obj, user):
        """Нельзя изменить объект стримера."""
        if obj.user.is_streamer:
            logger.warning(
                'Юзер %s (%s) попытался изменить объект %s стримера %s (%s)',
                user.username,
                user.role,
                obj.public_id,
                obj.user.username,
                obj.user.role,
            )
            raise ChangeObjValidationError(streamer=True)
