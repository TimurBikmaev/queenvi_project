from pathlib import Path
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
import pytest

from core.constants import TestConstants
from post.constants import MediaConstants as MC, MediaType, PostConstants
from post.models import Media, Post
from post.tests.constants import TestMediaConstants as TMC
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
    TestConstants.PARAMS_AUTH_USERS,
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


@pytest.mark.parametrize(
    'name, content_type',
    [
        ('test.mp4', 'video/mp4'),
        ('test.mp3', 'audio/mpeg'),
    ],
)
def test_post_patch_video_audio(
    auth, post_factory, file_factory, name, content_type
):
    old_post = post_factory()

    response = auth.patch(
        reverse('posts-detail', args=[old_post.public_id]),
        {'create_media': [file_factory(name=name, content_type=content_type)]},
        format='multipart',
    )

    assert response.status_code == HTTPStatus.OK, (
        'При обновлении поста должна быть возможность загружать: '
        f'{MC.FORMAT_AUDIO} + {MC.FORMAT_PHOTO} + {MC.FORMAT_VIDEO}'
    )

    media = Media.objects.get(post=old_post)
    extension = f'.{name.split(".")[TMC.EXTENSION_IDX]}'
    assert media.file.name.endswith(extension), (
        'При обновлении был отправлен один файл, а посту присвоился другой'
    )


@pytest.mark.django_db
def test_update_post_media_deletes_old_media(auth, post_factory, file_factory):
    post = post_factory()

    old_media = Media.objects.create(
        post=post,
        file=file_factory(),
        file_type=TMC.FORMAT,
        order=TMC.FIRST_MEDIA_IDX,
    )

    auth.patch(
        reverse('posts-detail', args=[post.public_id]),
        {
            'name': 'test',
            'create_media': [file_factory()]
        },
        format='multipart',
    )

    assert not Media.objects.filter(pk=old_media.pk).exists(), (
        'При обновление старое медиа у поста не удалилось из БД.'
    )

    assert Path((settings.MEDIA_ROOT)/'posts'/str(post.public_id)).exists(), (
        'При обновлении пост не создался каталог с медиа'
    )

    assert not Path(old_media.file.path).exists(), (
        'Старый файл не удалился из проекта'
    )

    new_media = Media.objects.filter(post=post)
    assert new_media.count() == TMC.ONE_MEDIA, (
        'При обновлении поста было присвоено неверное количество медиа.'
    )

    assert Path(new_media.first().file.path).exists(), (
        'Новый файл не сохранился в директории проекта.'
    )


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_NOT_STAFF,
)
def test_post_patch_cannot_anon_user_other_post(
    api_client, users, post_factory, role
):
    new_user = User.objects.create(
        username='new_user',
        role=UserRole.USER,
        twitch_id='new_user',
    )

    post = post_factory(new_user)

    if role is not None:
        api_client.force_authenticate(user=users[role])
    response = api_client.patch(
        reverse('posts-detail', args=[post.public_id]),
        {'name': 'test_2'},
        format='multipart',
    )

    assert response.status_code == HTTPStatus.FORBIDDEN, (
        'Аноним и обычный зареганный юзер не могут менять чужой пост'
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
    TestConstants.PARAMS_STAFF,
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

    assert post.is_banned == value, (
        'Модер и стример могут менять статус бана чужих постов'
    )


@pytest.mark.parametrize(
    'value',
    [True, False],
)
@pytest.mark.parametrize(
    'field',
    ['is_banned'],
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
    TestConstants.PARAMS_STAFF,
)
def test_post_patch_staff_cannot_unban_post_of_banned_user(
    api_client, users, post_factory, role
):
    old_post = post_factory()
    old_post.is_banned = True
    old_post.save(update_fields=['is_banned'])

    users[UserRole.USER].is_banned = True
    users[UserRole.USER].save(update_fields=['is_banned'])

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
    TestConstants.PARAMS_AUTH_USERS,
)
def test_post_patch_author_cannot_change_public_id_is_banned_of_his_post(
    api_client, users, post_factory, role
):
    old_post = post_factory(user=users[role])

    api_client.force_authenticate(user=users[role])
    response = api_client.patch(
        reverse('posts-detail', args=[old_post.public_id]),
        {
            'public_id': 'test',
            'is_banned': True
        },
        format='json',
    )

    assert response.data['public_id'] != 'test', 'Нельзя изменить "public_id"'
    assert 'is_banned' not in response.data, 'Нельзя забанить свой пост'


def test_post_patch_incorrect_name(auth, post_factory):
    old_post = post_factory()

    invalid_post_data = {'name': 't' * PostConstants.NAME_MAX_LENGTH + 't'}

    response = auth.patch(
        reverse('posts-detail', args=[old_post.public_id]),
        invalid_post_data,
        format='multipart',
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST, (
        f'Нельзя обновить пост с "name" > {PostConstants.NAME_MAX_LENGTH}'
    )


def test_post_patch_incorrect_description(auth, post_factory):
    old_post = post_factory()

    invalid_post_data = {
        'description': 't' * PostConstants.DESCRIPTION_MAX_LENGTH + 't',
    }

    response = auth.patch(
        reverse('posts-detail', args=[old_post.public_id]),
        invalid_post_data,
        format='multipart',
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST, (
        'Нельзя обновить пост с "description" '
        f'> {PostConstants.DESCRIPTION_MAX_LENGTH}'
    )


def test_post_patch_incorrect_files_min_count(auth, post_factory):
    old_post = post_factory()

    response = auth.patch(
        reverse('posts-detail', args=[old_post.public_id]),
        {'create_media': []},
        format='json',
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST, (
        f'Нельзя обновить пост с "media" < {PostConstants.MEDIA_MIN_COUNT}'
    )


def test_post_patch_incorrect_files_max_count(
        auth, post_factory, file_factory
):
    old_post = post_factory()

    response = auth.patch(
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


def test_patch_patch_incorrect_file_format(auth, post_factory, file_factory):
    old_post = post_factory()

    response = auth.patch(
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


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_BANNED_USERS,
)
def test_post_patch_by_banned(api_client, users, post_factory, role):
    users[role].is_banned = True
    users[role].save(update_fields=['is_banned'])

    post = post_factory(user=users[role])

    api_client.force_authenticate(user=users[role])
    response = api_client.patch(
        reverse('posts-detail', args=[post.public_id])
    )

    assert response.status_code == HTTPStatus.FORBIDDEN, (
        'Забаненный юзер не может изменять пост'
    )
