from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.urls import reverse
import pytest

from core.constants import TestConstants


User = get_user_model()


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_USERS,
)
def test_user_delete_not_allowed(api_client, users, role):
    if role is not None:
        api_client.force_authenticate(user=users[role])
    response = api_client.delete(reverse('profile-avatar'))

    if role is None:
        assert response.status_code == HTTPStatus.FORBIDDEN, (
            'Анониму не доступны чувствительные методы'
        )
        return

    assert response.status_code == HTTPStatus.BAD_REQUEST, (
        'Нельзя удалить другого юзера'
    )
