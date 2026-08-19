from http import HTTPStatus

import pytest
from django.urls import reverse

from post.models import Like
from core.constants import TestConstants
from post.tests.constants import TestLikeConstants as TLC


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_USERS,
)
def test_post_like_create_correct(api_client, users, post_factory, role):
    post = post_factory()

    if role is not None:
        api_client.force_authenticate(user=users[role])
    response = api_client.post(
        reverse('posts-like', args=[post.public_id]),
    )

    if role is None:
        assert response.status_code == HTTPStatus.FORBIDDEN, (
            'Аноним не может ставить лайк'
        )
        return

    assert response.status_code == HTTPStatus.OK

    assert Like.objects.filter(post=post, user=users[role]).exists(), (
        'Лайк не был создан'
    )

    assert response.data['likes_count'] == TLC.ONE_LIKE, (
        'При создании лайка счетчик лайков у поста не обновился'
    )


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_AUTH_USERS,
)
def test_post_like_create_same_post(api_client, users, post_factory, role):
    post = post_factory()

    api_client.force_authenticate(user=users[role])
    response = api_client.post(reverse('posts-like', args=[post.public_id]))

    assert response.status_code == HTTPStatus.OK

    assert response.data['likes_count'] == TLC.ONE_LIKE, (
        'Нельзя дважды лайкнуть пост'
    )


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_USERS,
)
def test_post_like_delete_correct(api_client, users, post_factory, role):
    post = post_factory()

    if role is not None:
        api_client.force_authenticate(user=users[role])
    response = api_client.delete(reverse('posts-like', args=[post.public_id]))

    if role is None:
        assert response.status_code == HTTPStatus.FORBIDDEN, (
            'Аноним не может удалить лайк'
        )
        return

    assert response.status_code == HTTPStatus.OK

    assert not Like.objects.filter(post=post, user=users[role]).exists(), (
        'Лайк не был удалён'
    )

    assert response.data['likes_count'] == TLC.NO_LIKES


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_BANNED_USERS,
)
def test_post_like_create_by_banned_user(
    api_client, users, post_factory, role
):
    post = post_factory()

    users[role].is_banned = True
    users[role].save(update_fields=['is_banned'])

    api_client.force_authenticate(user=users[role])

    response = api_client.post(reverse('posts-like', args=[post.public_id]))

    assert response.status_code == HTTPStatus.FORBIDDEN, (
        'Забаненный юзер не может ставить лайк'
    )


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_BANNED_USERS,
)
def test_post_like_delete_by_banned_user(
    api_client, users, post_factory, role,
):
    post = post_factory()

    users[role].is_banned = True
    users[role].save(update_fields=['is_banned'])

    api_client.force_authenticate(user=users[role])
    response = api_client.delete(reverse('posts-like', args=[post.public_id]))

    assert response.status_code == HTTPStatus.FORBIDDEN, (
        'Забаненный юзер не может удалить лайк'
    )
