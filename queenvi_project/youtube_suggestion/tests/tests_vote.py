from http import HTTPStatus

import pytest
from django.urls import reverse

from core.constants import TestConstants
from youtube_suggestion.tests.constants import TestVoteConstants as TVC
from youtube_suggestion.models import Voting


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_USERS,
)
def test_video_vote_create_correct(api_client, users, video_factory, role):
    video = video_factory()

    if role is not None:
        api_client.force_authenticate(user=users[role])
    response = api_client.post(
        reverse('videos-voting', args=[video.public_id]),
    )

    if role is None:
        assert response.status_code == HTTPStatus.FORBIDDEN, (
            'Аноним не может голосовать'
        )
        return

    assert response.status_code == HTTPStatus.OK

    assert Voting.objects.filter(video=video, user=users[role]).exists(), (
        'Лайк не был создан'
    )

    assert response.data['votings_count'] == TVC.ONE_VOTE, (
        'При создании лайка счетчик лайков у поста не обновился'
    )


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_AUTH_USERS,
)
def test_video_vote_create_same_video(api_client, users, video_factory, role):
    video = video_factory()

    api_client.force_authenticate(user=users[role])
    response = api_client.post(
        reverse('videos-voting', args=[video.public_id]))

    assert response.status_code == HTTPStatus.OK

    assert response.data['votings_count'] == TVC.ONE_VOTE, (
        'Нельзя дважды проголосовать за одно'
    )


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_USERS,
)
def test_video_vote_delete_correct(api_client, users, video_factory, role):
    video = video_factory()

    if role is not None:
        api_client.force_authenticate(user=users[role])
    response = api_client.delete(
        reverse('videos-voting', args=[video.public_id]))

    if role is None:
        assert response.status_code == HTTPStatus.FORBIDDEN, (
            'Аноним не может удалить голос'
        )
        return

    assert response.status_code == HTTPStatus.OK

    assert not Voting.objects.filter(video=video, user=users[role]).exists(), (
        'Голос не был удалён'
    )

    assert response.data['votings_count'] == TVC.NO_VOTES


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_BANNED_USERS,
)
def test_video_vote_create_by_banned_user(
    api_client, users, video_factory, role
):
    video = video_factory()

    users[role].is_banned = True
    users[role].save(update_fields=['is_banned'])

    api_client.force_authenticate(user=users[role])

    response = api_client.post(
        reverse('videos-voting', args=[video.public_id]))

    assert response.status_code == HTTPStatus.FORBIDDEN, (
        'Забаненный юзер не может голосовать'
    )


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_BANNED_USERS,
)
def test_video_vote_delete_by_banned_user(
    api_client, users, video_factory, role,
):
    video = video_factory()

    users[role].is_banned = True
    users[role].save(update_fields=['is_banned'])

    api_client.force_authenticate(user=users[role])
    response = api_client.delete(
        reverse('videos-voting', args=[video.public_id])
    )

    assert response.status_code == HTTPStatus.FORBIDDEN, (
        'Забаненный юзер не может удалить голос'
    )
