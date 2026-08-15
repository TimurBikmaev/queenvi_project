from http import HTTPStatus
from unittest.mock import patch

from django.urls import reverse
import pytest

from api.constants import SerializersConstants
from core.constants import TestConstants
from youtube_suggestion.constants import (
    Category, VideoServiceConstants as VSC, VideoConstants
)
from youtube_suggestion.models import Video


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_USERS,
)
def test_video_create_correct(api_client, users, role, mock_youtube_service):
    valid_video_data = {
        'youtube_url': 'https://youtu.be/-_tvzxLM_kM',
        'category': Category.HUMUROUS,
        'comment': 'test',
    }
    if role is not None:
        api_client.force_authenticate(user=users[role])
    response = api_client.post(
        reverse('videos-list'),
        valid_video_data,
        format='json',
    )

    if role is None:
        assert response.status_code == HTTPStatus.FORBIDDEN, (
            'Аноним не может предлагать видео'
        )
        return

    assert response.status_code == HTTPStatus.CREATED

    video_fields = [*SerializersConstants.VIDEO_BASE_FIELDS]
    assert set(video_fields) <= response.data.keys(), (
        'При создании видео не вернулись поля '
        f'{set(video_fields) - response.data.keys()}'
    )

    video = Video.objects.get(public_id=response.data['public_id'])
    assert video.user == users[role], (
        'При создании видео его автором стал юзер, который не делал запроса'
    )

    request_youtube_id = valid_video_data['youtube_url'][
        len(VSC.URL_VIDEO_YOUTUBE_2):
    ]
    assert len(video.youtube_id) == VideoConstants.VIDEO_ID_MAX_LENGTH, (
        'Длина присвоенного ID видео не соответствует стандартам YouTube'
    )
    assert request_youtube_id == video.youtube_id, (
        'Отправленное "youtube_id" и присвоенное не совпадают'
    )

    assert valid_video_data['category'] == video.category, (
        'Отправленная "category" и присвоенная не совпадают'
    )

    assert valid_video_data['comment'] == video.comment, (
        'Отправленный "comment" и присвоенный не совпадают'
    )


def test_video_create_default_value(auth, mock_youtube_service):
    valid_video_data = {
        'youtube_url': 'https://youtu.be/-_tvzxLM_kM',
        'category': Category.HUMUROUS,
    }

    response = auth.post(
        reverse('videos-list'),
        valid_video_data,
        format='json',
    )

    assert response.status_code == HTTPStatus.CREATED, response.data

    video = Video.objects.get(public_id=response.data['public_id'])

    assert video.comment == '', (
        'При создании видео без объявления "description" '
        'его значение должно быть ""'
    )

    assert video.is_banned is False, (
        'При создании видео значение "is_banned" должно быть False'
    )


@pytest.mark.parametrize(
    'field',
    ['youtube_url', 'category'],
)
@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_AUTH_USERS,
)
def test_video_create_required_fields(api_client, users, field, role):
    valid_video_data = {
        'youtube_url': 'https://youtu.be/-_tvzxLM_kM',
        'category': Category.HUMUROUS,
    }
    valid_video_data.pop(field)

    api_client.force_authenticate(user=users[role])
    response = api_client.post(
        reverse('videos-list'),
        valid_video_data,
        format='json',
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST

    assert field in response.data, (
        f'{field} является обязательным при создании видео'
    )


@pytest.mark.parametrize(
    'value',
    [
        'test',
        (
            VSC.URL_VIDEO_YOUTUBE_1 + 't'
            + 't' * VideoConstants.VIDEO_ID_MAX_LENGTH
        ),
        (
            VSC.URL_VIDEO_YOUTUBE_2 + 't'
            + 't' * VideoConstants.VIDEO_ID_MAX_LENGTH
        ),
    ],
)
def test_video_create_incorrect_youtube_url(auth, value):
    invalid_video_data = {
        'youtube_url': value,
        'category': Category.HUMUROUS,
    }

    response = auth.post(
        reverse('videos-list'),
        invalid_video_data,
        format='json',
    )

    msg = (
        'При создании видео "youtube_url" может начинаться только с '
        f'{VSC.URL_VIDEO_YOUTUBE_1} или {VSC.URL_VIDEO_YOUTUBE_2}'
    )
    if value != 'test':
        msg = (
            'Нельзя создать видео, если "youtube_id" '
            f'> {VideoConstants.VIDEO_ID_MAX_LENGTH}'
        )

    assert response.status_code == HTTPStatus.BAD_REQUEST, msg


def test_video_create_incorrect_category(auth):
    invalid_video_data = {
        'youtube_url': 'https://youtu.be/-_tvzxLM_kM',
        'category': 'test',
    }

    response = auth.post(
        reverse('videos-list'),
        invalid_video_data,
        format='json',
    )

    valid_categories = [category.value for category in Category]
    assert response.status_code == HTTPStatus.BAD_REQUEST, (
        f'Нельзя создавать видео, где категория не из {valid_categories}'
    )


def test_video_create_incorrect_comment(auth):
    invalid_video_data = {
        'youtube_url': 'https://youtu.be/-_tvzxLM_kM',
        'category': Category.HUMUROUS,
        'comment': 't' + 't' * VideoConstants.COMMENT_MAX_LENGTH
    }

    response = auth.post(
        reverse('videos-list'),
        invalid_video_data,
        format='json',
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST, (
        f'Нельзя пост с "comment" >  {VideoConstants.COMMENT_MAX_LENGTH}'
    )


def test_video_create_existed(auth, video_factory):
    video_factory(youtube_id='-_tvzxLM_kM')

    invalid_video_data = {
        'youtube_url': 'https://youtu.be/-_tvzxLM_kM',
        'category': Category.HUMUROUS,
    }

    response = auth.post(
        reverse('videos-list'),
        invalid_video_data,
        format='json',
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST, (
        'Нельзя создавать видео с одним и тем же youtube_id'
    )


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_AUTH_USERS,
)
def test_video_create_public_id_and_is_banned_change(
    api_client, users, role, mock_youtube_service
):
    request_public_id = 'тест'
    valid_video_data = {
        'public_id': request_public_id,
        'is_banned': True,
        'youtube_url': 'https://youtu.be/-_tvzxLM_kM',
        'category': Category.HUMUROUS,
    }

    api_client.force_authenticate(user=users[role])
    response = api_client.post(
        reverse('videos-list'),
        valid_video_data,
        format='json',
    )

    assert response.status_code == HTTPStatus.CREATED

    video = Video.objects.get(public_id=response.data['public_id'])

    assert video.public_id != request_public_id, (
        'Нельзя менять статус "public_id" при создании видео'
    )

    assert video.is_banned is False, (
        'Нельзя менять статус бана при создании видео'
    )


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_BANNED_USERS,
)
def test_video_create_by_banned(api_client, users, role):
    users[role].is_banned = True
    users[role].save(update_fields=['is_banned'])

    api_client.force_authenticate(user=users[role])
    response = api_client.post(
        reverse('posts-list'),
        {'youtube_id': 'test'}
    )

    assert response.status_code == HTTPStatus.FORBIDDEN, (
        'Забаненный юзер не может предлагать видео'
    )
