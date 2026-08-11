from http import HTTPStatus

from django.urls import reverse
import pytest

from api.constants import SerializersConstants
from post.constants import PostConstants
from user.constants import UserRole


@pytest.mark.parametrize(
    'role, has_private_field',
    [
        (None, False),
        (UserRole.USER, False),
        (UserRole.MODER, True),
        (UserRole.STREAMER, True),
    ],
)
def test_post_list(api_client, users, post_factory, role, has_private_field):
    post_factory(name='empty_desc')
    post_factory(description='12345678910')
    if role is not None:
        api_client.force_authenticate(user=users[role])
    response = api_client.get(reverse('posts-list'))
    assert response.status_code == HTTPStatus.OK
    for post in response.data:
        if post['name'] == 'empty_desc':
            assert 'description' not in post.keys(), (
                'Пустые строки не должны возвращаться в ответе'
            )
            continue
        post_fields = [*SerializersConstants.POST_BASE_FIELDS, 'preview']
        assert set(post_fields) <= post.keys(), (
            f'В посте отсутствуют поля {set(post_fields) - post.keys()}'
        )
        assert len(post['name']) <= PostConstants.NAME_PROFILEMAX_LENGTH, (
            'Длина "name" в ответе превышает допустимую'
        )
        assert (
            len(post['description'])
            <= PostConstants.DESCRIPTION_PROFILE_MAX_LENGTH
        ), ('Длина "description" в ответе превышает допустимую')
        assert isinstance(post['is_for_stream'], bool), (
            'Тип значения "is_for_stream" должно быть {bool}'
        )
        assert ('is_banned' in post) is has_private_field, (
            f'Видимость "is_banned" для юзера {role} - {'is_banned' in post}, '
            f'хотя должно быть {has_private_field}'
        )


# def test_post_list_ordering(api_client, post_factory):
#     post_factory(name='first', likes_count=1)
#     post_factory(name='second', likes_count=10)

#     response = api_client.get(
#         reverse('posts-list'),
#         {'ordering': '-likes_count'}
#     )

#     assert response.status_code == HTTPStatus.OK
#     assert response.data[0]['name'] == 'second'
#     assert response.data[1]['name'] == 'first'
