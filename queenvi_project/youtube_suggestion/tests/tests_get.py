from datetime import timedelta
from http import HTTPStatus

from django.urls import reverse
from django.utils import timezone
import pytest

from api.constants import SerializersConstants
from core.constants import TestConstants
from user.constants import UserRole
from youtube_suggestion.constants import Category
from youtube_suggestion.models import Voting
from youtube_suggestion.tests.constants import (
    MessageConstants, TestVideoConstants as TVC
)


@pytest.mark.parametrize(
    'role, has_private_field',
    [
        (None, False),
        (UserRole.USER, False),
        (UserRole.MODER, True),
        (UserRole.STREAMER, True),
    ],
)
def test_video_list_correct(
    api_client, users, video_factory, new_user, role, has_private_field
):
    video_factory(is_banned=True)

    video_factory(youtube_id='test_2')

    video_2 = video_factory(youtube_id='test_3')
    video_2.created_at = timezone.now() - timedelta(days=TVC.DELTA_DAYS_TWO)
    video_2.save(update_fields=['created_at'])

    video_3 = video_factory(youtube_id='test_4')

    video_4 = video_factory(youtube_id='test_5')

    Voting.objects.bulk_create([
        Voting(
            user=users[UserRole.USER],
            video=video_obj
        )
        for video_obj in (video_2, video_3, video_4)
    ])

    Voting.objects.create(user=new_user, video=video_4)

    if role is not None:
        api_client.force_authenticate(user=users[role])
    response = api_client.get(reverse('videos-list'))

    assert response.status_code == HTTPStatus.OK

    assert len(response.data) == TVC.FOUR_VIDEOS, (
        'Без фильтров забаненные видео не должны возвращаться'
    )

    assert (
        response.data[TVC.FIRST_VIDEO_IDX]['votings_count']
        > response.data[TVC.SECOND_VIDEO_IDX]['votings_count']
    ), 'По умолчанию видео должны быть отсортированы по убыванию голосов'

    assert (
        response.data[TVC.SECOND_VIDEO_IDX]['created_at']
        > response.data[TVC.THIRD_VIDEO_IDX]['created_at']
    ), (
        'По умолчанию видео c одинаковыми голосами '
        'должны быть отсортированы от новых к старым'
    )

    video_fields = [*SerializersConstants.VIDEO_BASE_FIELDS]
    assert set(video_fields) <= response.data[TVC.FIRST_VIDEO_IDX].keys(), (
        f'В видео отсутствуют поля {set(video_fields) - response.keys()}'
    )

    assert (
        ('is_banned' in response.data[TVC.FIRST_VIDEO_IDX].keys())
        is has_private_field
    ), (
        f'Видимость "is_banned" для юзера {role} '
        f'должна быть {has_private_field}'
    )


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_NOT_STAFF,
)
@pytest.mark.parametrize(
    'value',
    [True, False],
)
def test_video_list_is_voted_correct(
    api_client, users, video_factory, role, value
):
    video = video_factory()

    if role is not None:
        api_client.force_authenticate(user=users[role])
        if value is True:
            Voting.objects.create(user=users[role], video=video)
    videos = api_client.get(reverse('videos-list'))

    if role is None:
        assert videos.data[TVC.FIRST_VIDEO_IDX]['is_voted'] is False, (
            MessageConstants.IS_VOTED_ANONYMOUS
        )
        return

    if value is True:
        assert videos.data[TVC.FIRST_VIDEO_IDX]['is_voted'] is True, (
            MessageConstants.IS_VOTED_TRUE
        )
        return

    assert videos.data[TVC.FIRST_VIDEO_IDX]['is_voted'] is False, (
        MessageConstants.IS_VOTED_FALSE
    )


@pytest.mark.parametrize(
    'value',
    [category for category in Category.values if category != 'humurous'],
)
def test_video_list_filter_category(auth, video_factory, value):
    video_factory()
    video_factory(youtube_id='test_2', category=value)

    response = auth.get(reverse('videos-list'), {'category': value})

    assert len(response.data) == TVC.ONE_VIDEO, 'Фильтр "category" не работает'

    assert response.data[TVC.FIRST_VIDEO_IDX]['category'] == value, (
        'Фильтр "category" вернул видео с неверным значением фильтра'
    )


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_USERS,
)
@pytest.mark.parametrize(
    'value',
    ['all', True],
)
def test_video_list_filter_is_banned(
    api_client, users, video_factory, role, value
):
    video_factory()
    video_factory(youtube_id='test_2', is_banned=True)

    if role is not None:
        api_client.force_authenticate(user=users[role])
    response = api_client.get(reverse('videos-list'), {'is_banned': value})

    if role in (None, UserRole.USER):
        assert len(response.data) == TVC.ONE_VIDEO, (
            f'Фильтр is_banned для {role} не должен работать'
        )
        return

    if value == 'all':
        assert len(response.data) == TVC.TWO_VIDEOS, (
            f'Фильтр is_banned со значением {value} для {role} '
            'должен возвращать как забаненные, так и незабаненные видео'
        )
        return

    assert len(response.data) == TVC.ONE_VIDEO, (
        f'Фильтр is_banned со значениеем {value} для {role} не работает'
    )
    assert response.data[TVC.FIRST_VIDEO_IDX]['is_banned'] is value, (
        'Фильтр is_banned вернул пост с неверным значением фильтра'
    )


@pytest.mark.parametrize(
    'value',
    ['created_at', '-created_at'],
)
def test_video_list_ordering_created_at(auth, video_factory, value):
    video_1 = video_factory()
    video_1.created_at = timezone.now() - timedelta(days=TVC.DELTA_DAYS_TWO)
    video_1.save(update_fields=['created_at'])

    video_factory(youtube_id='test_2')

    response = auth.get(
        reverse('videos-list'),
        {'ordering': value}
    )

    first = response.data[TVC.FIRST_VIDEO_IDX]['created_at']
    second = response.data[TVC.SECOND_VIDEO_IDX]['created_at']

    if value == 'created_at':
        assert first < second, f'Сортировка для видео по {value} не работает'
    else:
        assert first > second, f'Сортировка для видео по {value} не работает'


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_BANNED_USERS,
)
def test_video_list_by_banned(api_client, users, video_factory, role):
    users[role].is_banned = True
    users[role].save(update_fields=['is_banned'])

    video = video_factory(user=users[role])

    api_client.force_authenticate(user=users[role])
    response = api_client.get(
        reverse('posts-detail', args=[video.public_id])
    )

    assert response.status_code == HTTPStatus.FORBIDDEN, (
        'Забаненный юзер не может смотреть предложку'
    )


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_USERS,
)
def test_video_retrieve_not_allowed(api_client, users, role, video_factory):
    video = video_factory()

    if role is not None:
        api_client.force_authenticate(user=users[role])
    response = api_client.get(
        reverse('videos-detail', args=[video.public_id])
    )

    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED, (
        'Retrieve для видео должен быть недоступен'
    )
