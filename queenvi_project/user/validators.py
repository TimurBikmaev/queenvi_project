from user.constants import UserRole
from user.errors import ChangeUserValidationError


class ChangeUserValidator:
    def user_cannot_change_himself(user, target):
        """Стример и модер не могут менять свои роли и статус бана."""
        if user == target:
            raise ChangeUserValidationError()

    def only_one_streamer(user, role):
        """Нельзя назначить второго стримера."""
        if user.is_streamer and role == UserRole.STREAMER:
            raise ChangeUserValidationError(streamer=True)

    def can_user_change_role(user):
        """Только стример может менять роль юзера."""
        if not user.is_streamer:
            raise ChangeUserValidationError(role=True)

    def can_user_change_is_banned(user, target):
        """Модер может забанить или разбанить только обычного юзера."""
        if user.is_moder and not target.is_user:
            raise ChangeUserValidationError(is_banned=True)
