from datetime import timedelta
from http import HTTPStatus

from django.urls import reverse
from django.utils import timezone
import pytest

from core.constants import TestConstants
from post.constants import CommentConstansts
from post.models import Comment
from post.tests.constants import TestCommentConstants as TCC


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_USERS,
)
def test_comment_list_correct(
    api_client, users, post_factory, comment_factory, new_user, role,
):
    post = post_factory()

    comment_factory()

    comment = comment_factory()
    comment.created_at = timezone.now() - timedelta(days=TCC.DELTA_TWO_DAYS)
    comment.save(update_fields=['created_at'])

    comment_factory(user=new_user)
    new_user.is_banned = True
    new_user.save(update_fields=['is_banned'])

    if role is not None:
        api_client.force_authenticate(user=users[role])
    response = api_client.get(reverse('comments-list', args=[post.public_id]))

    assert response.status_code == HTTPStatus.OK

    assert len(response.data) == TCC.TWO_COMMENTS, (
        'В списке комментов не должны отображаться комменты забаненных юзеров'
    )

    assert (
        response.data[TCC.FIRST_COMMENT_IDX]['created_at']
        > response.data[TCC.SECOND_COMMENT_IDX]['created_at']
    ), 'Комменты должны отсортированы от новых к старым'

    comment_fields = ['public_id', 'text', 'user', 'created_at', 'updated_at']
    assert (
        set(comment_fields) <= response.data[TCC.FIRST_COMMENT_IDX].keys()
    ), (
        'В комментах отсутствуют поля '
        f'{set(comment_fields) - response.data[TCC.FIRST_COMMENT_IDX].keys()}'
    )


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_USERS,
)
def test_comment_create_correct(api_client, post_factory, users, role, ):
    data = {'text': 'test2'}

    post = post_factory()

    if role is not None:
        api_client.force_authenticate(user=users[role])
    response = api_client.post(reverse(
        'comments-list', args=[post.public_id]),
        data,
        format='json'
    )

    if role is None:
        assert response.status_code == HTTPStatus.FORBIDDEN, (
            'Аноним не может создавать комменты'
        )
        return

    assert response.status_code == HTTPStatus.CREATED

    comment = Comment.objects.get(public_id=response.data['public_id'])

    assert comment.text == data['text'], (
        'При создании комменту был присвоен не тот текст'
    )
    assert comment.user == users[role], (
        'При создании комменту был присвоен не тот юзер'
    )
    assert comment.post == post, 'Коммент был создан в другом посте'


def test_comment_create_incorrect(auth, post_factory):
    post = post_factory()

    response = auth.post(reverse(
        'comments-list', args=[post.public_id]),
        {'text': 't' + 't' * CommentConstansts.TEXT_MAX_LENGTH},
        format='json'
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST, (
        'Нельзя создать комментарией с "text" '
        f'> {CommentConstansts.TEXT_MAX_LENGTH}'
    )


def test_comment_create_on_banned_post(auth, post_factory):
    post = post_factory(is_banned=True)

    response = auth.post(
        reverse('comments-list', args=[post.public_id]),
        {'text': 'test'},
        format='json',
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST, (
        'Нельзя комментировать забаненный пост'
    )


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_AUTH_USERS,
)
def test_comment_patch_correct(api_client, comment_factory, users, role):
    data = {
        'text': 'test2',
        'user': 'test',
        'post': 'test'
    }

    comment = comment_factory(user=users[role])
    user = comment.user
    post = comment.post

    api_client.force_authenticate(user=users[role])
    response = api_client.patch(
        reverse('comments-detail', args=[post.public_id, comment.public_id],),
        data,
        format='json'
    )

    assert response.status_code == HTTPStatus.OK

    comment.refresh_from_db()

    assert comment.text == data['text'], (
        'При обновлении комменту был присвоен не тот текст'
    )
    assert comment.user == user, (
        'При обновлении коммента нельзя изменить автора'
    )
    assert comment.post == post, (
        'Коммент при обновлении нельзя присвоить другому посту'
    )


def test_comment_patch_anon(api_client, comment_factory):
    data = {
        'text': 'test2',
        'user': 'test',
        'post': 'test'
    }

    comment = comment_factory()
    post = comment.post

    response = api_client.patch(
        reverse('comments-detail', args=[post.public_id, comment.public_id],),
        data,
        format='json'
    )

    assert response.status_code == HTTPStatus.FORBIDDEN, (
        'Аноним не может обновлять комменты'
    )


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_AUTH_USERS,
)
def test_comment_update_only_author(
    api_client, users, comment_factory, new_user, role,
):
    comment = comment_factory(user=new_user)
    post = comment.post

    api_client.force_authenticate(user=users[role])
    response = api_client.patch(
        reverse('comments-detail', args=[post.public_id, comment.public_id]),
        format='json'
    )

    assert response.status_code == HTTPStatus.FORBIDDEN, (
        'Нельзя изменять чужой коммент'
    )


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_AUTH_USERS,
)
def test_comment_delete_correct(api_client, users, comment_factory, role):
    comment = comment_factory(user=users[role])
    post = comment.post

    api_client.force_authenticate(users[role])
    response = api_client.delete(
        reverse('comments-detail', args=[post.public_id, comment.public_id])
    )

    assert response.status_code == HTTPStatus.NO_CONTENT

    assert not Comment.objects.filter(pk=comment.pk).exists()


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_AUTH_USERS,
)
def test_comment_delete_only_author(
    api_client, users, comment_factory, role, new_user
):
    comment = comment_factory(user=new_user)
    post = comment.post

    api_client.force_authenticate(users[role])
    response = api_client.delete(
        reverse('comments-detail', args=[post.public_id, comment.public_id])
    )

    assert response.status_code == HTTPStatus.FORBIDDEN, (
        'Только автор может удалять свои комменты'
    )


def test_comment_delete_anon(api_client, comment_factory):
    comment = comment_factory()
    post = comment.post

    response = api_client.delete(
        reverse('comments-detail', args=[post.public_id, comment.public_id])
    )

    assert response.status_code == HTTPStatus.FORBIDDEN, (
        'Аноним не может удалять посты'
    )


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_BANNED_USERS,
)
def test_comment_list_by_banned(api_client, users, comment_factory, role):
    comment = comment_factory()

    users[role].is_banned = True
    users[role].save(update_fields=['is_banned'])

    api_client.force_authenticate(user=users[role])
    response = api_client.get(
        reverse('comments-list', args=[comment.post.public_id])
    )

    assert response.status_code == HTTPStatus.FORBIDDEN, (
        'Забаненный юзер не может смотреть комменты'
    )


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_BANNED_USERS,
)
def test_comment_create_by_banned(api_client, users, comment_factory, role):
    comment = comment_factory()

    users[role].is_banned = True
    users[role].save(update_fields=['is_banned'])

    api_client.force_authenticate(user=users[role])
    response = api_client.post(
        reverse('comments-list', args=[comment.post.public_id])
    )

    assert response.status_code == HTTPStatus.FORBIDDEN, (
        'Забаненный юзер не может создать коммент'
    )


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_BANNED_USERS,
)
def test_comment_patch_by_banned(api_client, users, comment_factory, role):
    comment = comment_factory()
    post = comment.post

    users[role].is_banned = True
    users[role].save(update_fields=['is_banned'])

    api_client.force_authenticate(user=users[role])
    response = api_client.patch(
        reverse('comments-detail', args=[post.public_id, comment.public_id])
    )

    assert response.status_code == HTTPStatus.FORBIDDEN, (
        'Забаненный юзер не может обновлять коммент'
    )


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_BANNED_USERS,
)
def test_comment_delete_by_banned(api_client, users, comment_factory, role):
    comment = comment_factory()
    post = comment.post

    users[role].is_banned = True
    users[role].save(update_fields=['is_banned'])

    api_client.force_authenticate(user=users[role])
    response = api_client.delete(
        reverse('comments-detail', args=[post.public_id, comment.public_id])
    )

    assert response.status_code == HTTPStatus.FORBIDDEN, (
        'Забаненный юзер не может удалить коммент'
    )


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_USERS,
)
def test_comment_retrieve_not_allowed(api_client, users, comment_factory, role):
    comment = comment_factory()
    post = comment.post

    if role is not None:
        api_client.force_authenticate(user=users[role])
    response = api_client.get(
        reverse('comments-detail', args=[post.public_id, comment.public_id]),
    )

    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED, (
        'Retrieve для коммента недоступен'
    )
