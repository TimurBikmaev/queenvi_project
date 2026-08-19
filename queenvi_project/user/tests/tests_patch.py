from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
import pytest

from core.constants import TestConstants
from post.models import Media, Post
from post.tests.constants import TestMediaConstants as TMC
from user.constants import UserRole
from youtube_suggestion.constants import Category
from youtube_suggestion.models import Video
from youtube_suggestion.tests.constants import TestVideoConstants as TVC


User = get_user_model()


@pytest.mark.parametrize(
    'field, value',
    [
        ('twitch_id', 'test_2'),
        ('twitch_avatar', 'test_2'),
        ('role', UserRole.MODER),
        ('role', UserRole.STREAMER),
        ('is_banned', True),
        ('is_banned', False),
    ],
)
@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_USERS,
)
def test_user_patch_correct(
    api_client, users, image_factory, role, field, value
):
    new_user = User.objects.create(
        username='new_user',
        role=UserRole.USER,
        twitch_id='new_user',
    )
    old_field = getattr(new_user, field)

    if role is not None:
        api_client.force_authenticate(user=users[role])

    response = api_client.patch(
        reverse('profile-detail', args=[new_user.username]),
        {
            'custom_avatar': image_factory(),
            field: value
        },
    )

    if role in (None, UserRole.USER):
        assert response.status_code == HTTPStatus.FORBIDDEN, (
            f'Юзер {role} не должен иметь доступ к изменению любого профиля'
        )
        return

    elif role == UserRole.MODER and field == 'role':
        assert response.status_code == HTTPStatus.BAD_REQUEST, (
            'Модер не может менять роль другого юзера'
        )
        return

    elif role == UserRole.STREAMER and value == UserRole.STREAMER:
        assert response.status_code == HTTPStatus.BAD_REQUEST, (
            'Стример не может назначить второго стримера'
        )
        return

    assert response.status_code == HTTPStatus.OK

    new_user.refresh_from_db()

    if field not in ('role', 'is_banned'):
        assert getattr(new_user, field) == old_field, (
            f'Никто не может изменить {field} другого юзера'
        )
        return

    assert getattr(new_user, field) == value, (
        f'Юзер {role} может изменить {field} другого юзера'
    )


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_STAFF,
)
def test_user_patch_staff_cannot_change_himself(api_client, users, role):

    api_client.force_authenticate(user=users[role])
    response = api_client.patch(
        reverse('profile-detail', args=[users[role].username]),
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST, (
        'Модер и стример не могут изменять свою роль и статус бана'
    )


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_STAFF,
)
def test_user_patch_moder_cannot_change_staff(api_client, users, role):
    new_user = User.objects.create(
        username='new_user',
        role=role,
        twitch_id='new_user',
    )

    api_client.force_authenticate(user=users[UserRole.MODER])
    response = api_client.patch(
        reverse('profile-detail', args=[new_user.username]),
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST, (
        'Модер не может изменить другого модера или стримера'
    )


@pytest.mark.parametrize(
    'value',
    [True, False],
)
def test_user_patch_ban_user_ban_his_posts_videos(
        api_client, users, image_factory, value
):
    video = Video.objects.create(
        youtube_id='test',
        user=users[UserRole.USER],
        category=Category.HUMUROUS,
        title='test',
        preview_url='https://example.com/test-video',
        channel_name='test',
        pub_date=timezone.now(),
        duration=TVC.DURATION,
        views_count=TVC.COUNT_VIEWS,
        likes_count=TVC.COUNT_LIKES,
        comments_count=TVC.COUNT_COMMENTS,
    )

    post = Post.objects.create(name='test', user=users[UserRole.USER])
    Media.objects.create(
        post=post,
        file=image_factory(),
        file_type=TMC.FORMAT,
        order=TMC.FIRST_MEDIA_IDX
    )

    api_client.force_authenticate(user=users[UserRole.MODER])
    api_client.patch(
        reverse('profile-detail', args=[users[UserRole.USER].username]),
        {'is_banned': value}
    )

    post.refresh_from_db()
    video.refresh_from_db()

    if value is True:
        assert post.is_banned is True, (
            'При бане юзера должны баниться и его посты'
        )
        assert video.is_banned is True, (
            'При бане юзера должны баниться и его видео'
        )
        return

    assert post.is_banned is False, (
        'При разбане юзера должны разбаниться и его посты'
    )
    assert video.is_banned is False, (
        'При разбане юзера должны разбаниться и его видео'
    )


def test_user_patch_by_banned(api_client, users):
    users[UserRole.MODER].is_banned = True
    users[UserRole.MODER].save(update_fields=['is_banned'])

    api_client.force_authenticate(users[UserRole.MODER])
    response = api_client.patch(
        reverse('profile-detail', args=[users[UserRole.MODER].username]),
    )

    assert response.status_code == HTTPStatus.FORBIDDEN, (
        'Забаненный модер не может изменять ни свой ни чужой профиль'
    )
