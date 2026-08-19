from user.constants import UserConstants as UC


class AuthValidationError(Exception):
    msg = 'Не удалось выполнить вход через твич:('


class ChangeUserValidationError(Exception):

    def __init__(self, streamer=False, role=False, staff=False):
        msg = 'Нельзя изменить свою роль или статус бана :/'

        if streamer:
            msg = 'Нельзя назначить второго стримера :)'
        elif role:
            msg = 'Только стример может менять роли юзера!'
        elif staff:
            msg = 'Модератор может менять статус бана только у обычных юзеров!'

        super().__init__(msg)
