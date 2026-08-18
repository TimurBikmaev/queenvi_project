import logging
import secrets
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import get_user_model, login
import requests

from user.constants import TwitchLoginConstants
from user.errors import AuthValidationError


logger = logging.getLogger(__name__)
User = get_user_model()


class TwitchLoginService:
    """Аутентификация юзера через твич."""

    @staticmethod
    def get_login_url(request):
        """Формирование урла для аутентификации."""
        state = secrets.token_urlsafe(TwitchLoginConstants.LENGTH_STATE)
        request.session['oauth_state'] = state

        params = {
            'client_id': settings.TWITCH_CLIENT_ID,
            'redirect_uri': settings.TWITCH_REDIRECT_URI,
            'response_type': TwitchLoginConstants.TYPE_RESPONSE,
            'state': state,
        }

        return TwitchLoginConstants.URL_AUTH + urlencode(params)

    @staticmethod
    def authenticate(request):
        """Оркестрация аутентификации."""
        TwitchLoginService.check_state(request)
        access_token = TwitchLoginService.get_access_token(request)
        user_data = TwitchLoginService.get_user_data(access_token)

        return TwitchLoginService.create_user_from_twitch_data(
            request, user_data
        )

    @staticmethod
    def check_state(request):
        """Проверка, что логин и коллбэк односятся к одной сессии."""
        received_state = request.GET.get('state')
        saved_state = request.session.pop('oauth_state', None)

        if received_state != saved_state:
            logger.warning('Несовпадение OAuth state при аутентификации')
            raise AuthValidationError()

    @staticmethod
    def get_access_token(request):
        """Получение токена доступа для запроса к данным юзера."""
        auth_code = request.GET.get('code')

        try:
            response = requests.post(
                TwitchLoginConstants.URL_TOKEN,
                data={
                    'client_id': settings.TWITCH_CLIENT_ID,
                    'client_secret': settings.TWITCH_CLIENT_SECRET,
                    'code': auth_code,
                    'grant_type': TwitchLoginConstants.TYPE_GRAND,
                    'redirect_uri': settings.TWITCH_REDIRECT_URI,
                },
                timeout=TwitchLoginConstants.TIME_FOR_ANSWER,
            )
            response.raise_for_status()
        except requests.RequestException:
            logger.exception(
                'При получении токена доступа произошла сетевая ошибка'
            )
            raise AuthValidationError()

        access_token = response.json().get('access_token')

        if access_token is None:
            logger.error('Twitch не вернул access token')
            raise AuthValidationError()

        return f'Bearer {access_token}'

    @staticmethod
    def get_user_data(access_token):
        """Получение данных юзера из твича."""
        try:
            response = requests.get(
                TwitchLoginConstants.URL_USER_INFO,
                headers={
                    'Authorization': access_token,
                    'Client-Id': settings.TWITCH_CLIENT_ID,
                },
                timeout=TwitchLoginConstants.TIME_FOR_ANSWER,
            )
            response.raise_for_status()
            return response.json()['data'][TwitchLoginConstants.IDX_USER_DATA]
        except requests.RequestException:
            logger.exception(
                'При получении данных юзера произошла сетевая ошибка'
            )
            raise AuthValidationError()
        except (KeyError, IndexError, ValueError):
            logger.exception('Twitch вернул некорректные данные юзера')
            raise AuthValidationError()

    @staticmethod
    def create_user_from_twitch_data(request, data):
        """Создание или обновление юзера из данных твич-аккаунта."""
        user, created = User.objects.get_or_create(
            twitch_id=data['id'],
            defaults={
                'username': data['display_name'],
                'twitch_avatar': data['profile_image_url'],
            },
        )

        if created is True:
            user.set_unusable_password()
            user.save(update_fields=['password'])
            logger.info(
                'Создан новый юзер %s (%s) через OAuth Twitch',
                user.username,
                user.role
            )
        else:
            user.username = data['display_name']
            user.twitch_avatar = data['profile_image_url']
            user.save(update_fields=['username', 'twitch_avatar'])

        login(request, user)
        return user
