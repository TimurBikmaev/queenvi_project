import logging

from user.constants import UserRole
from user.errors import ChangeUserValidationError


logger = logging.getLogger(__name__)


class ChangeUserValidator:
    def user_cannot_change_himself(user, target):
        """Стример и модер не могут менять свои роли и статус бана."""
        if user == target:
            logger.warning(
                'Юзер %s (%s) попытался изменить свою роль или статус бана ',
                user.username,
                user.role
            )
            raise ChangeUserValidationError()

    def only_one_streamer(user, role, target):
        """Нельзя назначить второго стримера."""
        if user.is_streamer and role == UserRole.STREAMER:
            logger.warning(
                'Юзер %s (%s) попытался назначить '
                'юзера %s (%s) вторым стримером',
                user.username,
                user.role,
                target.username,
                target.role
            )
            raise ChangeUserValidationError(streamer=True)

    def can_user_change_role(user, target):
        """Только стример может менять роль юзера."""
        if not user.is_streamer:
            logger.warning(
                'Юзер %s (%s) попытался поменять роль юзера %s (%s)',
                user.username,
                user.role,
                target.username,
                target.role
            )
            raise ChangeUserValidationError(role=True)

    def can_user_change_other_user(user, target):
        """Модер может менять только обычного юзера."""
        if user.is_moder and not target.is_user:
            logger.warning(
                'Юзер %s | %s попытался изменить юзера %s | %s',
                user.username,
                user.role,
                target.username,
                target.role
            )
            raise ChangeUserValidationError(staff=True)
