from core.errors import ChangeObjValidationError


class ChangeBanStatusValidator:
    def cannot_unban_obj_of_banned_user(post):
        """Нельзя разбанить объект забаненного пользователя."""
        if post.user.is_banned and post.is_banned is True:
            raise ChangeObjValidationError()

    def cannot_change_streamer_obj(post):
        """Нельзя изменить объект стримера."""
        if post.user.is_streamer:
            raise ChangeObjValidationError(streamer=True)
