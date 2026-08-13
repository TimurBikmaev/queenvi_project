from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.urls import reverse
import pytest

from post.models import Post
from post.tests.constants import TestPostConstants as TPC
from user.constants import UserRole


User = get_user_model()


@pytest.mark.parametrize(
    'role',
    TPC.PARAMS_USER,
)
def test_post_delete_correct(api_client, users, post_factory, role):
    if role is None:
        post = post_factory()
    else:
        post = post_factory(users[role])
        api_client.force_authenticate(user=users[role])
    response = api_client.delete(
        reverse('posts-detail', args=[post.public_id]),
    )

    if role is None:
        assert response.status_code == HTTPStatus.FORBIDDEN, (
            'Аноним не может удалить пост'
        )
        return

    assert response.status_code == HTTPStatus.NO_CONTENT

    assert not Post.objects.filter(public_id=post.public_id).exists(), (
        'Пост не удалился'
    )


@pytest.mark.parametrize(
    'role',
    TPC.PARAMS_USER,
)
def test_post_delete_only_author(api_client, users, post_factory, role):
    new_user = User.objects.create(
        username='new_user',
        role=UserRole.USER,
        twitch_id='new_user',
    )
    post = post_factory(user=new_user)

    if role is not None:
        api_client.force_authenticate(user=users[role])
    response = api_client.delete(
        reverse('posts-detail', args=[post.public_id]),
    )

    assert response.status_code == HTTPStatus.FORBIDDEN

    assert Post.objects.filter(public_id=post.public_id).exists(), (
        'Только автор может удалить свой пост'
    )
