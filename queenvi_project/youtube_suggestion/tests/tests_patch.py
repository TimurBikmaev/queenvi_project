from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.urls import reverse
import pytest

from core.constants import TestConstants
from user.constants import UserRole
from youtube_suggestion.constants import Category, VideoConstants as VC
from youtube_suggestion.models import Video


User = get_user_model()


@pytest.mark.parametrize(
    'field, value',
    [
        ('category', Category.TRAILERS),
        ('comment', 'test_2'),
    ],
)
@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_AUTH_USERS,
)
def test_video_patch_correct(
    api_client, users, video_factory, role, field, value
):
    old_video = video_factory(user=users[role])

    api_client.force_authenticate(user=users[role])
    response = api_client.patch(
        reverse('videos-detail', args=[old_video.public_id]),
        {field: value},
        format='json',
    )

    assert response.status_code == HTTPStatus.OK

    video = Video.objects.get(public_id=response.data['public_id'])

    assert getattr(video, field) == value, f'Поле {field} не обновилось'


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_NOT_STAFF,
)
def test_video_patch_cannot_anon_user_other_video(
    api_client, users, video_factory, role
):
    new_user = User.objects.create(
        username='new_user',
        role=UserRole.USER,
        twitch_id='new_user',
    )

    video = video_factory(user=new_user)

    if role is not None:
        api_client.force_authenticate(user=users[role])
    response = api_client.patch(
        reverse('videos-detail', args=[video.public_id]),
        {'comment': 'test_2'},
        format='json',
    )

    assert response.status_code == HTTPStatus.FORBIDDEN, (
        'Аноним и обычный зареганный юзер не могут менять чужое видео'
    )


@pytest.mark.parametrize(
    'field, value',
    [
        ('category', Category.TRAILERS),
        ('comment', 'test_2'),
    ],
)
@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_STAFF,
)
def test_video_patch_ignore_fields_for_moder_streamer(
    api_client, users, video_factory, role, field, value
):
    old_video = video_factory()
    old_value = getattr(old_video, field)

    api_client.force_authenticate(user=users[role])
    response = api_client.patch(
        reverse('videos-detail', args=[old_video.public_id]),
        {field: value},
        format='json',
    )

    assert response.status_code == HTTPStatus.OK

    video = Video.objects.get(public_id=response.data['public_id'])

    assert getattr(video, field) == old_value, (
        f'Модер и стример не должны менять "{field}" чужого видео'
    )


@pytest.mark.parametrize(
    'field',
    ['is_banned'],
)
@pytest.mark.parametrize(
    'value',
    [True, False],
)
@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_STAFF,
)
def test_video_patch_moder_and_streamer_can_change_ban_status(
    api_client, video_factory, users, role, field, value
):
    new_user = User.objects.create(
        username='new_user',
        role=UserRole.USER,
        twitch_id='new_user',
    )
    old_video = video_factory(user=new_user)

    if value is False:
        old_video.is_banned = True
        old_video.save(update_fields=['is_banned'])

    api_client.force_authenticate(user=users[role])
    response = api_client.patch(
        reverse('videos-detail', args=[old_video.public_id]),
        {field: value},
        format='json',
    )

    assert response.status_code == HTTPStatus.OK

    video = Video.objects.get(public_id=response.data['public_id'])

    assert video.is_banned == value, (
        'Модер и стример могут менять статус бана чужих видео'
    )


@pytest.mark.parametrize(
    'value',
    [True, False],
)
@pytest.mark.parametrize(
    'field',
    ['is_banned'],
)
def test_video_patch_moder_cannot_ban_video_of_streamer(
    api_client, users, video_factory, field, value
):
    old_video = video_factory(user=users[UserRole.STREAMER])

    api_client.force_authenticate(user=users[UserRole.MODER])
    response = api_client.patch(
        reverse('videos-detail', args=[old_video.public_id]),
        {field: value},
        format='json',
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST, (
        'Модер не может менять статус бана видео стримера'
    )


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_STAFF,
)
def test_video_patch_staff_cannot_unban_video_of_banned_user(
    api_client, users, video_factory, role
):
    old_video = video_factory()
    old_video.is_banned = True
    old_video.save(update_fields=['is_banned'])

    users[UserRole.USER].is_banned = True
    users[UserRole.USER].save(update_fields=['is_banned'])

    api_client.force_authenticate(user=users[role])
    response = api_client.patch(
        reverse('videos-detail', args=[old_video.public_id]),
        {'is_banned': False},
        format='json',
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST, (
        f'{role} не может разбанить видео забаненного юзера'
    )


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_AUTH_USERS,
)
def test_video_patch_author_cannot_change_public_id_is_banned_of_his_video(
    api_client, users, video_factory, role
):
    old_video = video_factory(user=users[role])

    api_client.force_authenticate(user=users[role])
    response = api_client.patch(
        reverse('videos-detail', args=[old_video.public_id]),
        {
            'public_id': 'test',
            'is_banned': True
        },
        format='json',
    )

    assert response.data['public_id'] != 'test', 'Нельзя изменить "public_id"'
    assert 'is_banned' not in response.data, 'Нельзя забанить свое видео'


def test_video_patch_incorrect_category(auth, video_factory):
    old_video = video_factory()

    response = auth.patch(
        reverse('videos-detail', args=[old_video.public_id]),
        {'category': 'test'},
        format='json',
    )

    valid_categories = [category.value for category in Category]
    assert response.status_code == HTTPStatus.BAD_REQUEST, (
        f'Нельзя обновить "category", если она не из {valid_categories}'
    )


def test_video_patch_incorrect_comment(auth, video_factory):
    old_video = video_factory()

    response = auth.patch(
        reverse('videos-detail', args=[old_video.public_id]),
        {'comment': 't' + 't' * VC.COMMENT_MAX_LENGTH},
        format='json',
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST, (
        f'Нельзя обновить "comment", если он > {VC.COMMENT_MAX_LENGTH}'
    )


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_BANNED_USERS,
)
def test_video_patch_by_banned(api_client, users, video_factory, role):
    users[role].is_banned = True
    users[role].save(update_fields=['is_banned'])

    video = video_factory(user=users[role])

    api_client.force_authenticate(user=users[role])
    response = api_client.patch(
        reverse('posts-detail', args=[video.public_id])
    )

    assert response.status_code == HTTPStatus.FORBIDDEN, (
        'Забаненный юзер не может обновлять видео'
    )
