import pytest

from django.urls import reverse
from rest_framework import status

from post.models import Comment
from core.constants import PublicIdConstants
from user.constants import UserRole


COMMENTS_URL = 'comments-list'
COMMENT_DETAIL_URL = 'comments-detail'


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_USERS,
)
def test_comment_list_correct(
    api_client, users, post_factory, comment_factory, role,
):
    post = post_factory()
    comment = comment_factory(post=post)

    user = users.get(role)
    if user:
        api_client.force_authenticate(user=user)

    response = api_client.get(
        reverse(COMMENTS_URL, kwargs={'post_id': post.public_id})
    )

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]['public_id'] == str(comment.public_id)
    assert response.data[0]['text'] == comment.text
    assert response.data[0]['user']['public_id'] == str(comment.user.public_id)


def test_comment_list_ordered_by_created_at(
    api_client, post_factory, comment_factory,
):
    post = post_factory()

    old_comment = comment_factory(post=post)
    new_comment = comment_factory(post=post)

    response = api_client.get(
        reverse(COMMENTS_URL, kwargs={'post_id': post.public_id})
    )

    assert response.status_code == status.HTTP_200_OK
    assert [
        item['public_id'] for item in response.data
    ] == [
        str(new_comment.public_id),
        str(old_comment.public_id),
    ]


def test_comment_create_correct(
    api_client, users, post_factory,
):
    user = users[UserRole.USER]
    post = post_factory()

    api_client.force_authenticate(user=user)

    data = {'text': 'Очень хороший комментарий'}

    response = api_client.post(
        reverse(COMMENTS_URL, kwargs={'post_id': post.public_id}),
        data,
        format='json',
    )

    assert response.status_code == status.HTTP_201_CREATED

    comment = Comment.objects.get(public_id=response.data['public_id'])

    assert comment.text == data['text']
    assert comment.user == user
    assert comment.post == post


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_USERS,
)
def test_comment_create_unauthenticated_or_authenticated(
    api_client, users, post_factory, role,
):
    post = post_factory()

    user = users.get(role)
    if user:
        api_client.force_authenticate(user=user)

    response = api_client.post(
        reverse(COMMENTS_URL, kwargs={'post_id': post.public_id}),
        {'text': 'Комментарий'},
        format='json',
    )

    if user:
        assert response.status_code == status.HTTP_201_CREATED
    else:
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_comment_create_on_banned_post_not_allowed(
    api_client, users, post_factory,
):
    user = users[UserRole.USER]
    post = post_factory(is_banned=True)

    api_client.force_authenticate(user=user)

    response = api_client.post(
        reverse(COMMENTS_URL, kwargs={'post_id': post.public_id}),
        {'text': 'Комментарий'},
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data == 'Нельзя комментировать забаненный пост'


@pytest.mark.parametrize(
    'role',
    [UserRole.USER, UserRole.MODER, UserRole.STREAMER],
)
def test_comment_update_owner(
    api_client, users, post_factory, comment_factory, role,
):
    user = users[role]
    post = post_factory()
    comment = comment_factory(post=post, user=user)

    api_client.force_authenticate(user=user)

    response = api_client.patch(
        reverse(
            COMMENT_DETAIL_URL,
            kwargs={'post_id': post.public_id, 'public_id': comment.public_id},
        ),
        {'text': 'Измененный комментарий'},
        format='json',
    )

    assert response.status_code == status.HTTP_200_OK

    comment.refresh_from_db()
    assert comment.text == 'Измененный комментарий'


def test_comment_update_not_owner(
    api_client, users, post_factory, comment_factory,
):
    owner = users[UserRole.USER]
    other_user = users[UserRole.USER_2]  # если есть такой enum

    post = post_factory()
    comment = comment_factory(post=post, user=owner)

    api_client.force_authenticate(user=other_user)

    response = api_client.patch(
        reverse(
            COMMENT_DETAIL_URL,
            kwargs={'post_id': post.public_id, 'public_id': comment.public_id},
        ),
        {'text': 'Чужой комментарий'},
        format='json',
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_comment_delete_owner(
    api_client, users, post_factory, comment_factory,
):
    user = users[UserRole.USER]
    post = post_factory()
    comment = comment_factory(post=post, user=user)

    api_client.force_authenticate(user=user)

    response = api_client.delete(
        reverse(
            COMMENT_DETAIL_URL,
            kwargs={'post_id': post.public_id, 'public_id': comment.public_id},
        ),
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Comment.objects.filter(pk=comment.pk).exists()


def test_comment_delete_not_owner(
    api_client, users, post_factory, comment_factory,
):
    owner = users[UserRole.USER]
    other_user = users[UserRole.MODER]

    post = post_factory()
    comment = comment_factory(post=post, user=owner)

    api_client.force_authenticate(user=other_user)

    response = api_client.delete(
        reverse(
            COMMENT_DETAIL_URL,
            kwargs={'post_id': post.public_id, 'public_id': comment.public_id},
        ),
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert Comment.objects.filter(pk=comment.pk).exists()
