from http import HTTPStatus

from django.urls import reverse
import pytest

from core.constants import TestConstants


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_USERS,
)
def test_video_delete_not_allowed(api_client, users, video_factory, role):
    if role is None:
        video = video_factory()
    else:
        video = video_factory(user=users[role])
        api_client.force_authenticate(user=users[role])
    response = api_client.delete(
        reverse('videos-detail', args=[video.public_id]),
    )

    if role is None:
        assert response.status_code == HTTPStatus.FORBIDDEN, (
            'Метод delete должен быть недоступен для анонима'
        )
        return

    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED, (
        'Никто не может удалить видео из предложки'
    )
