import secrets
from urllib.parse import urlencode

from django.conf import settings
import requests
from rest_framework.exceptions import ValidationError

from core.constants import TwitchLoginConstants
from user.models import User


class TwitchLoginService:
    """Аутентификация юзера через твич."""

    @staticmethod
    def get_login_url(request):
        """Формирование урла для аутентификации."""
        state = secrets.token_urlsafe(TwitchLoginConstants.LENGTH_STATE)
        request.session["oauth_state"] = state
        params = {
            "client_id": settings.TWITCH_CLIENT_ID,
            "redirect_uri": settings.TWITCH_REDIRECT_URI,
            "response_type": TwitchLoginConstants.TYPE_RESPONSE,
            # "scope": TwitchLoginConstants.SCOPE,
            "state": state,
        }
        return TwitchLoginConstants.URL_AUTH + urlencode(params)

    @staticmethod
    def authenticate(request):
        "Оркестрация аутентификации."
        TwitchLoginService.check_state(request)
        access_token = TwitchLoginService.get_access_token(request)
        user_data = TwitchLoginService.get_user_data(access_token)
        return TwitchLoginService.create_user_from_twitch_data(user_data)

    @staticmethod
    def check_state(request):
        """Проверка, что логин и коллбэк односятся к одной сессии."""
        received_state = request.GET.get('state')
        saved_state = request.session.pop("oauth_state", None)
        if received_state != saved_state:
            raise ValidationError("Не удалось выполнить вход через твич:(")

    @staticmethod
    def get_access_token(request):
        """Получение токена доступа для запроса к данным юзера."""
        auth_code = request.GET.get('code')
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
        data = response.json()
        return f'Bearer {data.get("access_token")}'

    @staticmethod
    def get_user_data(access_token):
        """Получение данных юзера из твича."""
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

    @staticmethod
    def create_user_from_twitch_data(data):
        """Создание юзера из данных твич-аккаунта."""
        user, created = User.objects.get_or_create(
            twitch_id=data["id"],
            defaults={
                "username": data["display_name"],
                "twitch_avatar": data["profile_image_url"],
            },
        )
        if not created:
            user.username = data["display_name"]
            user.twitch_avatar = data["profile_image_url"]
            user.save(update_fields=["username", "twitch_avatar"])

        return user
