from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.urls import reverse
import pytest

from post.constants import MediaConstants as MC, MediaType, PostConstants
from post.models import Post
from post.tests.constants import (
    TestMediaConstants as TMC, TestPostConstants as TPC,
)
from user.constants import UserRole


User = get_user_model()


@pytest.mark.parametrize(
    'field, value',
    [
        ('name', 'test_2'),
        ('description', 'test_2'),
        ('is_for_stream', False),
        ('create_media', None),
    ],
)
@pytest.mark.parametrize(
    'role',
    TPC.PARAMS_AUTH_USER,
)
def test_post_patch_correct(
    api_client, users, post_factory, file_factory, role, field, value
):
    old_post = post_factory(users[role])

    valid_post_data = {field: value}
    if field == 'create_media':
        valid_post_data = {'create_media': [file_factory(name='test_2.jpg')]}

    api_client.force_authenticate(user=users[role])
    response = api_client.patch(
        reverse('posts-detail', args=[old_post.public_id]),
        valid_post_data,
        format='multipart',
    )

    assert response.status_code == HTTPStatus.OK

    post = Post.objects.get(public_id=response.data['public_id'])

    if field == 'create_media':
        uploaded_files = valid_post_data['create_media']
        post_files = post.media.order_by('order')

        assert len(uploaded_files) == post_files.count(), (
            f'При создании поста было отправлено {len(uploaded_files)} файла, '
            f'а пост создался с {post_files.count()}'
        )

        for uploaded_file, post_file in zip(uploaded_files, post_files):
            uploaded_file.seek(TMC.READ_FILE_FROM_BEGIN)
            post_file.file.open('rb')
            assert uploaded_file.read() == post_file.file.read(), (
                'Отправленные при создании поста файлы не совпадают с теми,'
                'что присвоились посту после patch (возможно, они отображены '
                'не в том порядке, в каком их загружали при создании)'
            )
            assert post_file.file_type == MediaType.PHOTO, (
                'У загруженного файла неверно определен "file_type"'
            )
            return

    assert getattr(post, field) == value, f'Поле {field} не обновилось'


def test_post_patch_anon_cannot(api_client, post_factory):
    post = post_factory()

    response = api_client.patch(
        reverse('posts-detail', args=[post.public_id]),
        {'name': 'test_2'},
        format='multipart',
    )

    assert response.status_code == HTTPStatus.FORBIDDEN, (
        'Аноним не может изменять пост'
    )


def test_post_patch_only_author(api_client, post_factory):
    post = post_factory()

    new_user = User.objects.create(
        username='new_user',
        role=UserRole.USER,
        twitch_id='new_user',
    )

    api_client.force_authenticate(user=new_user)
    response = api_client.patch(
        reverse('posts-detail', args=[post.public_id]),
        {'name': 'test_2'},
        format='multipart',
    )

    assert response.status_code == HTTPStatus.FORBIDDEN, (
        'За исключением модера и стримера только автор может изменять пост'
    )


@pytest.mark.parametrize(
    'field, value',
    [
        ('name', 'test_2'),
        ('description', 'test_2'),
        ('is_for_stream', False),
        ('create_media', None),
    ],
)
@pytest.mark.parametrize(
    'role',
    TPC.PARAMS_STAFF,
)
def test_post_patch_ignore_fields_for_moder_streamer(
    api_client, users, post_factory, file_factory, role, field, value
):
    old_post = post_factory()
    if field != 'create_media':
        old_attr = getattr(old_post, field)

    valid_post_data = {field: value}
    if field == 'create_media':
        valid_post_data = {
            'create_media': [file_factory(content=b'old content')]
        }

    api_client.force_authenticate(user=users[role])
    response = api_client.patch(
        reverse('posts-detail', args=[old_post.public_id]),
        valid_post_data,
        format='multipart',
    )

    assert response.status_code == HTTPStatus.OK

    post = Post.objects.get(public_id=response.data['public_id'])

    if field == 'create_media':
        uploaded_files = valid_post_data['create_media']
        post_files = post.media.order_by('order')

        for uploaded_file, post_file in zip(uploaded_files, post_files):
            uploaded_file.seek(TMC.READ_FILE_FROM_BEGIN)
            post_file.file.open('rb')
            assert uploaded_file.read() != post_file.file.read(), (
                'Модер и стример не могут менять медиа чужого поста'
            )
            return

    assert getattr(post, field) == old_attr, (
        f'Модер и стример не должны менять "{field}" чужого поста'
    )


@pytest.mark.parametrize(
    'field, value',
    [
        ('is_banned', True),
        ('is_banned', False),
    ],
)
@pytest.mark.parametrize(
    'role',
    TPC.PARAMS_STAFF,
)
def test_post_patch_moder_and_streamer_can_change_ban_status(
    api_client, users, post_factory, role, field, value
):
    new_user = User.objects.create(
        username='new_user',
        role=UserRole.USER,
        twitch_id='new_user',
    )
    old_post = post_factory(new_user)

    if value is False:
        old_post.is_banned = True
        old_post.save(update_fields=['is_banned'])

    api_client.force_authenticate(user=users[role])
    response = api_client.patch(
        reverse('posts-detail', args=[old_post.public_id]),
        {field: value},
        format='multipart',
    )

    assert response.status_code == HTTPStatus.OK

    post = Post.objects.get(public_id=response.data['public_id'])

    assert old_post.is_banned != post.is_banned, (
        'Модер и стример могут менять статус бана чужих постов'
    )


@pytest.mark.parametrize(
    'field, value',
    [
        ('is_banned', True),
        ('is_banned', False),
    ],
)
def test_post_patch_moder_cannot_сhange_ban_status_of_streamer(
    api_client, users, post_factory, field, value
):
    old_post = post_factory(user=users[UserRole.STREAMER])

    api_client.force_authenticate(user=users[UserRole.MODER])
    response = api_client.patch(
        reverse('posts-detail', args=[old_post.public_id]),
        {field: value},
        format='multipart',
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST, (
        'Модер не может банить пост стримера'
    )


@pytest.mark.parametrize(
    'role',
    TPC.PARAMS_STAFF,
)
def test_post_patch_staff_cannot_unban_post_of_banned_user(
    api_client, users, post_factory, role
):
    old_post = post_factory()
    old_post.is_banned = True
    old_post.save(update_fields=['is_banned'])

    users[UserRole.USER].is_banned = True
    users[UserRole.USER].save(update_fields=['is_banned'])

    assert old_post.is_banned is True
    assert users[UserRole.USER].is_banned is True

    api_client.force_authenticate(user=users[role])
    response = api_client.patch(
        reverse('posts-detail', args=[old_post.public_id]),
        {'is_banned': False},
        format='multipart',
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST, (
        f'{role} не может разбанить пост забаненного юзера'
    )


@pytest.mark.parametrize(
    'role',
    TPC.PARAMS_AUTH_USER,
)
def test_post_patch_author_cannot_ban_his_post(
    api_client, users, post_factory, role
):
    old_post = post_factory(user=users[role])

    api_client.force_authenticate(user=users[role])
    response = api_client.patch(
        reverse('posts-detail', args=[old_post.public_id]),
        {'is_banned': True},
        format='multipart',
    )

    assert 'is_banned' not in response.data, ('Нельзя забанить свой пост')


def test_post_update_incorrect_name(api_client, post_factory, users):
    old_post = post_factory()

    invalid_post_data = {'name': 't' * PostConstants.NAME_MAX_LENGTH + 't'}

    api_client.force_authenticate(user=users[UserRole.USER])
    response = api_client.patch(
        reverse('posts-detail', args=[old_post.public_id]),
        invalid_post_data,
        format='multipart',
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST, (
        f'Нельзя обновить пост с "name" > {PostConstants.NAME_MAX_LENGTH}'
    )


def test_post_update_incorrect_description(api_client, users, post_factory):
    old_post = post_factory()

    invalid_post_data = {
        'description': 't' * PostConstants.DESCRIPTION_MAX_LENGTH + 't',
    }

    api_client.force_authenticate(user=users[UserRole.USER])
    response = api_client.patch(
        reverse('posts-detail', args=[old_post.public_id]),
        invalid_post_data,
        format='multipart',
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST, (
        'Нельзя обновить пост с "description" '
        f'> {PostConstants.DESCRIPTION_MAX_LENGTH}'
    )


def test_post_update_incorrect_files_min_count(
        api_client, users, post_factory
):
    old_post = post_factory()

    api_client.force_authenticate(user=users[UserRole.USER])
    response = api_client.patch(
        reverse('posts-detail', args=[old_post.public_id]),
        {'create_media': []},
        format='json',
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST, (
        f'Нельзя обновить пост с "media" < {PostConstants.MEDIA_MIN_COUNT}'
    )


def test_post_patch_incorrect_files_max_count(
    api_client, users, post_factory, file_factory
):
    old_post = post_factory()

    api_client.force_authenticate(user=users[UserRole.USER])
    response = api_client.patch(
        reverse('posts-detail', args=[old_post.public_id]),
        {
            'create_media': [
                file_factory(name=str(x))
                for x in range(PostConstants.MEDIA_MAX_COUNT + TMC.ONE_MEDIA)
            ],
        },
        format='multipart',
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST, (
        f'Нельзя обновить пост с "media" > {PostConstants.MEDIA_MAX_COUNT}'
    )


def test_patch_create_incorrect_file_format(
        api_client, users, post_factory, file_factory
):
    old_post = post_factory()

    api_client.force_authenticate(user=users[UserRole.USER])
    response = api_client.patch(
        reverse('posts-detail', args=[old_post.public_id]),
        {
            'create_media': [file_factory(name='test.txt')],
        },
        format='multipart',
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST, (
        'В пост можно загружать файлы только таких форматов: '
        f'{MC.FORMAT_AUDIO + MC.FORMAT_PHOTO + MC.FORMAT_VIDEO}'
    )
