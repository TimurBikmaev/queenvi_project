from django.contrib.auth import get_user_model
import pytest
from rest_framework.test import APIClient

from user.constants import UserRole


User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def users(db):
    return {
        role: User.objects.create(
            twitch_id=role,
            username=role,
            role=role,
            twitch_avatar='test'
        )
        for role in UserRole
    }


@pytest.fixture
def auth(api_client, users):
    api_client.force_authenticate(user=users[UserRole.USER])
    return api_client


@pytest.fixture
def moder(api_client, users):
    api_client.force_authenticate(user=users[UserRole.MODER])
    return api_client


@pytest.fixture
def new_user(db):
    return User.objects.create(
        twitch_id='new_user',
        username='new_user',
        role=UserRole.USER,
        twitch_avatar='new_user'
    )
