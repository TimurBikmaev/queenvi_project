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
            username=role,
            role=role,
            twitch_id=role,
        )
        for role in UserRole
    }
