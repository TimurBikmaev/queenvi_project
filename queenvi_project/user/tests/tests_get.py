from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.urls import reverse
import pytest

from core.constants import TestConstants
from user.constants import UserRole


User = get_user_model()


@pytest.mark.parametrize(
    'role, has_private_field',
    [
        (None, False),
        (UserRole.USER, False),
        (UserRole.MODER, True),
        (UserRole.STREAMER, True),
    ],
)
def test_user_retrieve_correct(api_client, users, role, has_private_field):
    if role is not None:
        api_client.force_authenticate(user=users[role])
    response = api_client.get(
        reverse('profile-detail', args=[users[UserRole.USER].username])
    )

    assert response.status_code == HTTPStatus.OK

    user_fields = [
        'twitch_avatar', 'username', 'posts_count',
        'posts', 'created_at', 'updated_at'
    ]
    assert set(user_fields) <= response.data.keys(), (
        f'В профиле отсутствуют поля {set(user_fields) - response.data.keys()}'
    )

    assert ('role' in response.data) is has_private_field, (
        f'Видимость "role" для юзера {role} должна быть {has_private_field}'
    )

    assert ('is_banned' in response.data) is has_private_field, (
        f'Видимость "is_banned" для юзера {role}  '
        f'должна быть {has_private_field}'
    )


def test_user_retrieve_custom_avatar(auth, image_factory):
    new_user = User.objects.create(
        twitch_id='test',
        username='test',
        role=UserRole.USER,
        twitch_avatar='test',
        custom_avatar=image_factory()
    )
    response = auth.get(
        reverse('profile-detail', args=[new_user.username])
    )

    assert (
        'twitch_avatar' not in response.data
        and response.data['custom_avatar']
    ), 'Если в профиле кастомная авка, то твичовская не должна возвращаться'


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_USERS,
)
def test_user_retrieve_banned_for_users(api_client, users, role):
    new_user = User.objects.create(
        username='test',
        twitch_id='test',
        twitch_avatar='test'
    )
    new_user.is_banned = True
    new_user.save(update_fields=['is_banned'])

    if role is not None:
        api_client.force_authenticate(user=users[role])
    response = api_client.get(
        reverse('profile-detail', args=[new_user.username])
    )

    if role in (None, UserRole.USER):
        assert response.status_code == HTTPStatus.NOT_FOUND, (
            'Запрос забаненного профиля для анонима/юзера должен быть 404'
        )
        return

    assert response.status_code == HTTPStatus.OK

    assert response.data['is_banned'] is True, (
        f'Юзер {role} должен иметь возможность видеть забаненный профиль'
    )


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_BANNED_USERS,
)
def test_banned_user_cannot_retrieve_profile(api_client, users, role):
    users[role].is_banned = True
    users[role].save(update_fields=['is_banned'])

    api_client.force_authenticate(user=users[role])

    response = api_client.get(
        reverse('profile-detail', args=[users[role].username])
    )

    assert response.status_code == HTTPStatus.FORBIDDEN, (
        'Забаненный юзер не может смотреть профили'
    )


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_USERS,
)
def test_user_list_not_allowed(api_client, users, role):
    if role is not None:
        api_client.force_authenticate(user=users[role])
    response = api_client.get('api/v1/profile/')

    assert response.status_code == HTTPStatus.NOT_FOUND, (
        'Метода list для просмотра профилей не должно быть'
    )
