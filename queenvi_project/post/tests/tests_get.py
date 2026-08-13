from http import HTTPStatus

from django.urls import reverse
import pytest

from api.constants import SerializersConstants
from post.constants import PostConstants
from post.models import Comment, Like
from post.tests.constants import (
    TestMediaConstants as TMC, MessageConstants, TestPostConstants as TPC,
)
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
def test_post_list_correct(
    api_client, users, post_factory, role, has_private_field
):
    post_factory(name='empty_desc')
    post_factory(is_banned=True)
    post_factory(description='12345678910')

    if role is not None:
        api_client.force_authenticate(user=users[role])
    response = api_client.get(reverse('posts-list'))

    assert response.status_code == HTTPStatus.OK
    assert len(response.data) == TPC.TWO_POSTS, (
        'Без фильтров забаненные посты не должны возвращаться'
    )
    assert (
        response.data[TPC.FIRST_POST_IDX]['created_at']
        > response.data[TPC.SECOND_POST_IDX]['created_at']
    ), 'По умолчанию посты должны быть отсортированы от новых к старым'

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
            'Длина "name" у постов в профиле превышает допустимую'
        )
        assert (
            len(post['description'])
            <= PostConstants.DESCRIPTION_PROFILE_MAX_LENGTH
        ), 'Длина "description" у постов в профиле превышает допустимую'

        assert ('is_banned' in post) is has_private_field, (
            f'Видимость "is_banned" для юзера {role} - {'is_banned' in post}, '
            f'хотя должно быть {has_private_field}'
        )


@pytest.mark.parametrize(
    'role',
    TPC.PARAMS_USER,
)
def test_post_list_preview_order(
    api_client, users, role, post_many_files
):
    if role is not None:
        api_client.force_authenticate(user=users[role])
    response = api_client.get(reverse('posts-list'))

    response_preview = response.data[TMC.FIRST_MEDIA_IDX]['preview']
    post_preview = post_many_files.media.order_by('order').first()

    assert response_preview['file'].endswith(post_preview.file.name), (
        'Превью должно быть первым файлом, загруженным юзером'
    )


@pytest.mark.parametrize(
    'role, value',
    TPC.PARAMS_FILTER,
)
def test_post_list_is_liked_correct(
    api_client, users, post_factory, role, value
):
    post = post_factory()

    if role is not None:
        api_client.force_authenticate(user=users[role])
        if value is True:
            Like.objects.create(user=users[role], post=post)
    posts_list = api_client.get(reverse('posts-list'))

    if role is None:
        assert posts_list.data[TPC.FIRST_POST_IDX]['is_liked'] is False, (
            MessageConstants.IS_LIKED_ANONYMOUS
        )
        return

    if value is True:
        assert posts_list.data[TPC.FIRST_POST_IDX]['is_liked'] is True, (
            MessageConstants.IS_LIKED_TRUE
        )
        return

    assert posts_list.data[TPC.FIRST_POST_IDX]['is_liked'] is False, (
        MessageConstants.IS_LIKED_FALSE
    )


@pytest.mark.parametrize(
    'role, value',
    TPC.PARAMS_FILTER,
)
def test_post_list_filter_is_for_stream(
    api_client, users, post_factory, role, value
):
    post_factory(is_for_stream=False)
    post_factory()

    if role is not None:
        api_client.force_authenticate(user=users[role])
    response = api_client.get(reverse('posts-list'), {'is_for_stream': value})

    assert len(response.data) == TPC.ONE_POST, (
        'Фильтр is_for_stream не работает'
    )
    assert response.data[TPC.FIRST_POST_IDX]['is_for_stream'] is value, (
        'Фильтр is_for_stream вернул пост с неверным значением фильтра'
    )


@pytest.mark.parametrize(
    'role, value',
    TPC.PARAMS_FILTER + [
        (None, 'all'),
        (UserRole.USER, 'all'),
        (UserRole.MODER, 'all'),
        (UserRole.STREAMER, 'all'),
    ],
)
def test_post_list_filter_is_banned(
    api_client, users, post_factory, role, value
):
    post_factory(is_banned=True)
    post_factory()

    if role is not None:
        api_client.force_authenticate(user=users[role])
    response = api_client.get(reverse('posts-list'), {'is_banned': value})

    if role in (None, UserRole.USER):
        assert len(response.data) == TPC.ONE_POST, (
            f'Фильтр is_banned для {role} не должен работать'
        )
        return

    if value == 'all':
        assert len(response.data) == TPC.TWO_POSTS, (
            f'Фильтр is_banned со значением {value} для {role} '
            'должен возвращать как забаненные, так и незабаненные посты'
        )
        return

    assert len(response.data) == TPC.ONE_POST, (
        f'Фильтр is_banned со значениеем {value} для {role} не работает'
    )
    assert response.data[TPC.FIRST_POST_IDX]['is_banned'] is value, (
        'Фильтр is_banned вернул пост с неверным значением фильтра'
    )


@pytest.mark.parametrize(
    'role',
    TPC.PARAMS_USER,
)
def test_post_list_ordering_likes_comments_count(
    api_client, users, post_factory, role
):
    post_factory()
    post = post_factory()
    Like.objects.create(post=post, user=users[UserRole.USER])
    Comment.objects.create(post=post, user=users[UserRole.USER])

    if role is not None:
        api_client.force_authenticate(user=users[role])
    response_likes = api_client.get(
        reverse('posts-list'),
        {'ordering': '-likes_count'}
    )
    response_comments = api_client.get(
        reverse('posts-list'),
        {'ordering': '-comments_count'}
    )

    assert (
        response_likes.data[TPC.FIRST_POST_IDX]['likes_count'] == TPC.ONE_LIKE
        and
        response_likes.data[TPC.SECOND_POST_IDX]['likes_count'] == TPC.NO_LIKES
    ), 'Посты не соответствуют сортировке likes_count=True'
    assert (
        response_comments.data[TPC.FIRST_POST_IDX]['comments_count']
        == TPC.ONE_COMMENT
        and
        response_comments.data[TPC.SECOND_POST_IDX]['comments_count']
        == TPC.NO_COMMENTS
    ), 'Посты не соответствуют сортировке comments_count=True'


@pytest.mark.parametrize(
    'role',
    TPC.PARAMS_USER,
)
def test_post_retrieve_correct(api_client, users, role, post_many_files):
    if role is not None:
        api_client.force_authenticate(user=users[role])
    response = api_client.get(
        reverse('posts-detail', args=[post_many_files.public_id])
    )

    assert response.status_code == HTTPStatus.OK

    post_fields = [*SerializersConstants.POST_BASE_FIELDS, 'media']
    assert set(post_fields) <= response.data.keys(), (
        f'В посте отсутствуют поля {set(post_fields) - response.data.keys()}'
    )

    files = response.data['media']
    assert [file['order'] for file in files] == [
        TMC.FIRST_MEDIA_IDX, TMC.SECOND_MEDIA_IDX, TMC.THIRD_MEDIA_IDX
    ], 'Медиа в посте должны находиться в порядке, в котором их загружали'


@pytest.mark.parametrize(
    'role',
    TPC.PARAMS_USER,
)
def test_post_retrieve_banned_for_moder_or_streamer(
    api_client, users, post_factory, role
):
    post = post_factory(is_banned=True)

    if role is not None:
        api_client.force_authenticate(user=users[role])
    response = api_client.get(reverse('posts-detail', args=[post.public_id]))

    if role in (None, UserRole.USER):
        assert response.status_code == HTTPStatus.NOT_FOUND, (
            'Запрос забаненного поста для анонима/юзера должен быть 404'
        )
        return

    assert response.status_code == HTTPStatus.OK
    assert response.data['is_banned'] is True, (
        f'Юзеру {role} должен видеть статус бана поста'
    )


@pytest.mark.parametrize(
    'role',
    TPC.PARAMS_USER,
)
def test_post_retrieve_without_empty_string(
    api_client, users, post_factory, role
):
    post = post_factory()

    if role is not None:
        api_client.force_authenticate(user=users[role])
    response = api_client.get(reverse('posts-detail', args=[post.public_id]))

    assert 'description' not in response.data.keys(), (
        'Пустые строки не должны возвращаться в ответе'
    )


@pytest.mark.parametrize(
    'role, value',
    TPC.PARAMS_FILTER,
)
def test_post_retrieve_is_liked_correct(
    api_client, users, post_factory, role, value
):
    post = post_factory()

    if role is not None:
        api_client.force_authenticate(user=users[role])
        if value is True:
            Like.objects.create(user=users[role], post=post)
    post_detail = api_client.get(
        reverse('posts-detail', args=[post.public_id])
    )

    if role is None:
        assert post_detail.data['is_liked'] is False, (
            MessageConstants.IS_LIKED_ANONYMOUS
        )
        return

    if value is True:
        assert post_detail.data['is_liked'] is True, (
            MessageConstants.IS_LIKED_TRUE
        )
        return

    assert post_detail.data['is_liked'] is False, (
        MessageConstants.IS_LIKED_FALSE
    )
