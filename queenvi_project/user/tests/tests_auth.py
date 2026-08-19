from http import HTTPStatus
from unittest.mock import patch

from django.urls import reverse
import pytest

from core.constants import TestConstants
from user.constants import TwitchLoginConstants, UserRole


@patch('api.views.TwitchLoginService.get_login_url')
def test_user_twitch_login(mock_get_login_url, api_client):
    mock_get_login_url.return_value = TwitchLoginConstants.URL_AUTH

    response = api_client.get(reverse('profile-twitch-login'))

    assert response.status_code == HTTPStatus.FOUND

    assert response.url == TwitchLoginConstants.URL_AUTH, (
        'При переходе на twitch-login должен быть '
        'редирект на OAuth-страницу Twitch'
    )


@patch('api.views.TwitchLoginService.authenticate')
def test_twitch_callback(mock_authenticate, api_client, users):
    mock_authenticate.return_value = users[UserRole.USER]

    response = api_client.get(reverse('profile-twitch-callback'))

    assert response.status_code == HTTPStatus.FOUND

    assert response.url == reverse(
        'profile-detail',
        args=[users[UserRole.USER].username]
    ), 'После аутентификации должен быть редирект на профиль пользователя'


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_USERS,
)
def test_user_auth_logout(api_client, users, role):
    if role is not None:
        api_client.force_authenticate(users[role])
    response = api_client.post(reverse('profile-logout'))

    if role is None:
        assert response.status_code == HTTPStatus.FORBIDDEN, (
            'Аноним не должен иметь возможности разлогиниться'
        )
        return

    assert response.status_code == HTTPStatus.FOUND, (
        f'Юзер {role} не смог разлогиниться'
    )
