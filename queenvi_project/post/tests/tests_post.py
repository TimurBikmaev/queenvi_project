from pathlib import Path
from http import HTTPStatus

from django.conf import settings
from django.urls import reverse
import pytest

from api.constants import SerializersConstants
from core.constants import TestConstants
from post.constants import MediaConstants as MC, MediaType, PostConstants
from post.models import Post
from post.tests.constants import TestMediaConstants as TMC


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_USERS,
)
def test_post_create_correct(api_client, users, file_factory, role,):
    valid_post_data = {
        'name': 'test',
        'description': 'test',
        'is_for_stream': False,
        'create_media': [file_factory(), file_factory(name='test_2.jpg')],
    }

    if role is not None:
        api_client.force_authenticate(user=users[role])
    response = api_client.post(
        reverse('posts-list'),
        valid_post_data,
        format='multipart',
    )

    if role is None:
        assert response.status_code == HTTPStatus.FORBIDDEN, (
            'Аноним не может создавать посты'
        )
        return

    assert response.status_code == HTTPStatus.CREATED

    post_fields = [*SerializersConstants.POST_BASE_FIELDS, 'media']
    assert set(post_fields) <= response.data.keys(), (
        'При создании поста не вернулись поля '
        f'{set(post_fields) - response.data.keys()}'
    )

    post = Post.objects.get(public_id=response.data['public_id'])
    assert post.user == users[role], (
        'При создании поста его автором стал юзер, который не делал запроса'
    )

    assert post.name == valid_post_data['name'], (
        f'"name" при создании поста был "{valid_post_data['name']}", '
        f'а стал {post.name}'
    )

    assert post.description == valid_post_data['description'], (
        '"description" при создании поста был '
        f'"{valid_post_data['description']}", а стал {post.description}'
    )

    assert post.is_for_stream == valid_post_data['is_for_stream'], (
        '"is_for_stream" при создании поста был '
        f'"{valid_post_data['is_for_stream']}", а стал {post.is_for_stream}'
    )

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
            'что присвоились посту после create (возможно, они отображены '
            'не в том порядке, в каком их загружали при создании)'
        )
        assert post_file.file_type == MediaType.PHOTO, (
            'У загруженного файла неверно определен "file_type"'
        )
        assert Path(post_file.file.path).exists(), (
            'Новый файл не сохранился в директории проекта.'
        )

    assert Path((settings.MEDIA_ROOT)/'posts'/str(post.public_id)).exists(), (
        'При создании поста не создался каталог с медиа'
    )


@pytest.mark.parametrize(
    'name, content_type',
    [
        ('test.mp4', 'video/mp4'),
        ('test.mp3', 'audio/mpeg'),
    ],
)
def test_post_create_video_audio(auth, file_factory, name, content_type):
    response = auth.post(
        reverse('posts-list'),
        {
            'name': 'test',
            'create_media': [
                file_factory(name=name, content_type=content_type),
            ]
        },
        format='multipart',
    )

    assert response.status_code == HTTPStatus.CREATED, (
        'При создании поста должна быть возможность загружать: '
        f'{MC.FORMAT_AUDIO} + {MC.FORMAT_PHOTO} + {MC.FORMAT_VIDEO}'
    )

    media = response.data['media'][TMC.FIRST_MEDIA_IDX]
    assert media['file'].endswith(f'.{name.split(".")[TMC.EXTENSION_IDX]}'), (
        'При создании был отправлен один файл, а посту присвоился другой'
    )


def test_post_create_default_value(auth, file_factory):
    valid_post_data = {
        'name': 'test',
        'create_media': [file_factory()],
    }

    response = auth.post(
        reverse('posts-list'),
        valid_post_data,
        format='multipart',
    )

    assert response.status_code == HTTPStatus.CREATED

    post = Post.objects.get(public_id=response.data['public_id'])

    assert post.description == '', (
        'При создании поста без объявления "description" '
        'его значение должно быть ""'
    )

    assert post.is_for_stream is True, (
        'При создании поста без объявления "is_for_stream" '
        'его значение должно быть True'
    )

    assert post.is_banned is False, (
        'При создании поста значение "is_banned" должно быть False'
    )


@pytest.mark.parametrize(
    'field',
    ['name', 'create_media'],
)
@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_AUTH_USERS,
)
def test_post_create_required_fields(
    api_client, users, field, role, file_factory
):
    valid_post_data = {
        'name': 'test',
        'create_media': [file_factory()],
    }
    valid_post_data.pop(field)

    api_client.force_authenticate(user=users[role])
    response = api_client.post(
        reverse('posts-list'),
        valid_post_data,
        format='multipart',
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST

    assert field in response.data, (
        f'{field} является обязательным при создании поста'
    )


def test_post_create_incorrect_name(auth, file_factory):
    invalid_post_data = {
        'name': 't' * PostConstants.NAME_MAX_LENGTH + 't',
        'create_media': [file_factory()],
    }

    response = auth.post(
        reverse('posts-list'),
        invalid_post_data,
        format='multipart',
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST, (
        f'Нельзя создавать пост с "name" > {PostConstants.NAME_MAX_LENGTH}'
    )


def test_post_create_incorrect_description(auth, file_factory):
    invalid_post_data = {
        'name': 'test',
        'description': 't' * PostConstants.DESCRIPTION_MAX_LENGTH + 't',
        'create_media': [file_factory()],
    }

    response = auth.post(
        reverse('posts-list'),
        invalid_post_data,
        format='multipart',
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST, (
        'Нельзя создавать пост с "description" '
        f'> {PostConstants.DESCRIPTION_MAX_LENGTH}'
    )


def test_post_create_incorrect_files_min_count(auth):
    invalid_post_data = {
        'name': 'test',
        'create_media': [],
    }

    response = auth.post(
        reverse('posts-list'),
        invalid_post_data,
        format='multipart',
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST, (
        f'Нельзя создавать пост с "media" < {PostConstants.MEDIA_MIN_COUNT}'
    )


def test_post_create_incorrect_files_max_count(auth, file_factory):
    invalid_post_data = {
        'name': 'test',
        'create_media': [
            file_factory(name=str(x))
            for x in range(PostConstants.MEDIA_MAX_COUNT + TMC.ONE_MEDIA)
        ],
    }

    response = auth.post(
        reverse('posts-list'),
        invalid_post_data,
        format='multipart',
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST, (
        f'Нельзя создавать пост с "media" > {PostConstants.MEDIA_MAX_COUNT}'
    )


def test_post_create_incorrect_file_format(auth, file_factory):
    invalid_post_data = {
        'name': 'test',
        'create_media': [file_factory(name='test.txt')],
    }

    response = auth.post(
        reverse('posts-list'),
        invalid_post_data,
        format='multipart',
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST, (
        'В пост можно загружать файлы только таких форматов: '
        f'{MC.FORMAT_AUDIO + MC.FORMAT_PHOTO + MC.FORMAT_VIDEO}'
    )


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_AUTH_USERS,
)
def test_post_create_public_id_and_is_banned_change(
    api_client, users, file_factory, role
):
    request_public_id = 'тест'
    valid_post_data = {
        'public_id': request_public_id,
        'name': 'test',
        'is_banned': True,
        'create_media': [file_factory()],
    }

    api_client.force_authenticate(user=users[role])
    response = api_client.post(
        reverse('posts-list'),
        valid_post_data,
        format='multipart',
    )

    assert response.status_code == HTTPStatus.CREATED

    post = Post.objects.get(public_id=response.data['public_id'])
    assert post.public_id != request_public_id, (
        'Нельзя менять статус "public_id" при создании поста'
    )
    assert post.is_banned is False, (
        'Нельзя менять статус бана при создании поста'
    )


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_BANNED_USERS,
)
def test_post_create_by_banned(api_client, users, file_factory, role):
    users[role].is_banned = True
    users[role].save(update_fields=['is_banned'])

    api_client.force_authenticate(user=users[role])
    response = api_client.post(
        reverse('posts-list'),
        {
            'name': 'test',
            'create_media': file_factory()
        }
    )

    assert response.status_code == HTTPStatus.FORBIDDEN, (
        'Забаненный юзер не может создать пост'
    )
