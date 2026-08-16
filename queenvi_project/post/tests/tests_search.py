from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.urls import reverse
import pytest

from core.constants import TestConstants
from post.constants import PostConstants
from post.tests.constants import TestPostConstants as TPC
from user.constants import UserRole
from user.tests.constants import TestUserConstants as TUC


User = get_user_model()


@pytest.mark.parametrize(
    'role',
    TestConstants.PARAMS_USERS,
)
def test_search(
    api_client, users, post_factory, role
):
    post_name = 'Superswordmega'
    post_factory(name=post_name)
    post_factory(name='Другой пост')

    User.objects.create(
        username='aloha',
        role=UserRole.USER,
        twitch_id='queen_vi',
    )
    User.objects.create(
        username='swordex',
        role=UserRole.USER,
        twitch_id='another_user',
    )

    if role is not None:
        api_client.force_authenticate(user=users[role])
    response = api_client.get(reverse('search'), {'find': 'word'})

    assert response.status_code == HTTPStatus.OK

    find_posts_name = response.data['posts'][TPC.FIRST_POST_IDX]['name']
    find_username = response.data['users'][TUC.FIRST_USER_IDX]['username']

    assert len(response.data['posts']) == TPC.ONE_POST, (
        'Поиск находит лишние или не все искомые посты'
    )
    assert (
        find_posts_name == post_name[:PostConstants.NAME_PROFILE_MAX_LENGTH]
    ), 'Поиск обнаружил не искомый пост'

    assert (len(response.data['users'][TUC.FIRST_USER_IDX])) == TUC.ONE_USER, (
        'Поиск возвращает лишних или не всех искомых юзеров'
    )
    assert find_username == 'swordex', 'Поиск обнаружил не искомого юзера'
