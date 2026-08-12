from http import HTTPStatus

from django.urls import reverse
import pytest

from api.constants import SerializersConstants
from post.constants import PostConstants
from post.models import Comment, Like
from post.tests.constants import ListPostConstants as LPC
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
    assert len(response.data) == LPC.TWO_POSTS, (
        'Без фильтров забаненные посты не должны возвращаться'
    )
    assert (
        response.data[LPC.FIRST_POST_IDX]['created_at']
        > response.data[LPC.SECOND_POST_IDX]['created_at']
    ), 'По умолчанию посты должны быть отсортированы от новым к старым'

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
        ), 'Длина "description" в ответе превышает допустимую'

        assert ('is_banned' in post) is has_private_field, (
            f'Видимость "is_banned" для юзера {role} - {'is_banned' in post}, '
            f'хотя должно быть {has_private_field}'
        )


@pytest.mark.parametrize(
    'role, value',
    LPC.FILTER_PARAMS,
)
def test_post_is_liked_correct(api_client, users, post_factory, role, value):
    post = post_factory()

    if role is not None:
        api_client.force_authenticate(user=users[role])
        if value is True:
            Like.objects.create(user=users[role], post=post)
    response = api_client.get(reverse('posts-list'))

    if role is None:
        assert response.data[LPC.FIRST_POST_IDX]['is_liked'] is False, (
            'Значение поле is_liked для анонима всегда должно быть False'
        )
        return

    if value is True:
        assert response.data[LPC.FIRST_POST_IDX]['is_liked'] is True, (
            'Значение поля is_liked False, хотя юзер лайкнул пост'
        )
        return

    assert response.data[LPC.FIRST_POST_IDX]['is_liked'] is False, (
        'Значение поля is_liked True, хотя юзер не лайкал пост'
    )


@pytest.mark.parametrize(
    'role, value',
    LPC.FILTER_PARAMS,
)
def test_post_list_filter_is_for_stream(
    api_client, users, post_factory, role, value
):
    post_factory(is_for_stream=False)
    post_factory()

    if role is not None:
        api_client.force_authenticate(user=users[role])
    response = api_client.get(reverse('posts-list'), {'is_for_stream': value})

    assert len(response.data) == LPC.ONE_POST, (
        'Фильтр is_for_stream не работает'
    )
    assert response.data[LPC.FIRST_POST_IDX]['is_for_stream'] is value, (
        'Фильтр is_for_stream вернул пост с неверным значением фильтра'
    )


@pytest.mark.parametrize(
    'role, value',
    LPC.FILTER_PARAMS + [
        (None, 'all'),
        (UserRole.USER, 'all'),
        (UserRole.MODER, 'all'),
        (UserRole.STREAMER, 'all'),
    ]
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
        assert len(response.data) == LPC.ONE_POST, (
            f'Фильтр is_banned для {role} не должен работать'
        )
        return

    if value == 'all':
        assert len(response.data) == LPC.TWO_POSTS, (
            f'Фильтр is_banned со значением {value} для {role} '
            'должен возвращать как забаненные, так и незабаненные посты'
        )
        return

    assert len(response.data) == LPC.ONE_POST, (
        f'Фильтр is_banned со значениеем {value} для {role} не работает'
    )
    assert response.data[LPC.FIRST_POST_IDX]['is_banned'] is value, (
        'Фильтр is_banned вернул пост с неверным значением фильтра'
    )


@pytest.mark.parametrize(
    'role',
    [
        (None),
        (UserRole.USER),
        (UserRole.MODER),
        (UserRole.STREAMER),
    ],
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
        response_likes.data[LPC.FIRST_POST_IDX]['likes_count'] == LPC.ONE_LIKE
        and
        response_likes.data[LPC.SECOND_POST_IDX]['likes_count'] == LPC.NO_LIKES
    ), 'Посты не соответствуют сортировке likes_count=True'
    assert (
        response_comments.data[LPC.FIRST_POST_IDX]['comments_count']
        == LPC.ONE_COMMENT
        and
        response_comments.data[LPC.SECOND_POST_IDX]['comments_count']
        == LPC.NO_COMMENTS
    ), 'Посты не соответствуют сортировке comments_count=True'
