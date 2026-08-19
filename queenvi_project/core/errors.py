class ChangeObjValidationError(Exception):

    def __init__(self, streamer=False):
        msg = 'Нельзя разбанить объект забаненного пользователя :/'

        if streamer is True:
            msg = 'Нельзя менять статус бана объекта стримера :)'

        super().__init__(msg)
