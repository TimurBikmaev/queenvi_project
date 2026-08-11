from http import HTTPStatus

from django.urls import reverse
import pytest

from api.constants import SerializersConstants
from user.constants import UserRole


@pytest.mark.parametrize(
    'role, has_private_field',
    [
        (UserRole.USER, False),
        (UserRole.MODER, True),
        (UserRole.STREAMER, True),
    ],
)
def test_get_post(api_client, users, posts, role, has_private_field):
    api_client.force_authenticate(user=users[role])
    response = api_client.get(reverse('posts-list'))
    assert response.status_code == HTTPStatus.OK
    for post in response.data:
        post_fields = [*SerializersConstants.POST_BASE_FIELDS, 'preview']
        assert set(post_fields) <= post.keys()
        assert len(post['name']) >=
        assert ('is_banned' in post) == has_private_field
