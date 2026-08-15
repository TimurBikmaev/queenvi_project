from http import HTTPStatus

from django.urls import reverse
import pytest

from core.constants import TestConstants
from user.constants import UserConstants as UC
from user.tests.constants import TestMediaConstants as TMC


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_USERS,
)
def test_user_avatar_patch_correct(api_client, users, role, image_factory):
    image = image_factory()

    if role is not None:
        old_twitch_avatar = users[role].twitch_avatar
        api_client.force_authenticate(user=users[role])
    response = api_client.patch(
        reverse('profile-avatar'),
        {
            'twitch_avatar': 'test_2',
            'custom_avatar': image
        },
        format='multipart',
    )

    if role is None:
        assert response.status_code == HTTPStatus.FORBIDDEN, (
            'Аноним не может менять авку'
        )
        return

    assert response.status_code == HTTPStatus.OK

    users[role].refresh_from_db()
    assert users[role].twitch_avatar == old_twitch_avatar, (
        'Нельзя изменить твичовскую авку, для этого есть кастомная'
    )

    assert 'twitch_avatar' not in response.data, (
        'При обновлении кастомной авки твичовская не должна возвращаться'
    )

    image.seek(TMC.READ_FILE_FROM_BEGIN)

    users[role].refresh_from_db()

    with users[role].custom_avatar.open('rb') as avatar:
        assert avatar.read() == image.read(), (
            'Переданная кастомная авка не присвоена юзеру'
        )


@pytest.mark.parametrize(
    'file_attr, value',
    [
        ('extra_size', UC.AVATAR_MAX_SIZE),
        ('resolution', (
            UC.AVATAR_MAX_WIDTH + TMC.EXTRA_PIXEL,
            UC.AVATAR_MAX_HEIGHT + TMC.EXTRA_PIXEL,
        ))
    ],
)
def test_user_avatar_patch_incorrect_image(
    auth, image_factory, file_attr, value
):
    new_image = image_factory(**{file_attr: value})

    response = auth.patch(
        reverse('profile-avatar'),
        {'custom_avatar': new_image},
        format='multipart',
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST, (
        f'Нельзя загрузить авку с {file_attr} - {value}'
    )


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_USERS,
)
def test_user_avatar_delete_correct(api_client, users, role, image_factory):
    if role is not None:
        old_twitch_avatar = users[role].twitch_avatar
        users[role].custom_avatar = image_factory()
        users[role].save(update_fields=['custom_avatar'])

        api_client.force_authenticate(users[role])
    response = api_client.delete(reverse('profile-avatar'))

    if role is None:
        assert response.status_code == HTTPStatus.FORBIDDEN, (
            'Аноним не может удалить авку'
        )
        return

    assert response.status_code == HTTPStatus.OK

    users[role].refresh_from_db()

    assert users[role].twitch_avatar == old_twitch_avatar, (
        'Нельзя удалить твичевскую авку'
    )

    assert 'twitch_avatar' in response.data, (
        'После удаления кастомной авки, должна возвращаться твичовская'
    )

    assert not users[role].custom_avatar, (
        'После удаления кастомная авка должен отсутствовать у юзера'
    )


def test_user_avatar_delete_not_existed_custom_avatar(auth):
    response = auth.delete(reverse('profile-avatar'))

    assert response.status_code == HTTPStatus.BAD_REQUEST, (
        'Нельзя удалить несуществующую авку'
    )


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_BANNED_USERS,
)
def test_user_avatar_patch_cannot_by_banned(
    api_client, users, role, image_factory
):
    users[role].is_banned = True
    users[role].save(update_fields=['is_banned'])

    api_client.force_authenticate(user=users[role])
    response = api_client.patch(
        reverse('profile-avatar'),
        {'custom_avatar': image_factory()},
        format='multipart',
    )

    assert response.status_code == HTTPStatus.FORBIDDEN, (
        f'Забаненный {role} не может изменять аватар'
    )


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_BANNED_USERS,
)
def test_user_avatar_delete_cannot_by_banned(
    api_client, users, role, image_factory
):
    users[role].is_banned = True
    users[role].save(update_fields=['is_banned'])

    api_client.force_authenticate(user=users[role])
    response = api_client.delete(reverse('profile-avatar'))

    assert response.status_code == HTTPStatus.FORBIDDEN, (
        f'Забаненный {role} не может удалить авку'
    )
