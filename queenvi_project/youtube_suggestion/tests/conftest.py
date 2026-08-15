from django.utils import timezone
import pytest

from user.constants import UserRole
from youtube_suggestion.constants import Category
from youtube_suggestion.models import Video
from youtube_suggestion.tests.constants import TestVideoConstants as TVC


@pytest.fixture
def video_factory(db, users):
    def create(
            youtube_id='test',
            user=users[UserRole.USER],
            category=Category.HUMUROUS,
            comment='test',
            is_banned=False,
            created_at=None,
    ):
        video = Video.objects.create(
            youtube_id=youtube_id,
            user=user,
            category=category,
            comment=comment,
            is_banned=is_banned,
            created_at=created_at,
            title='test',
            preview_url='https://example.com/test-video',
            channel_name='test',
            pub_date=timezone.now(),
            duration=TVC.DURATION,
            views_count=TVC.COUNT_VIEWS,
            likes_count=TVC.COUNT_LIKES,
            comments_count=TVC.COUNT_COMMENTS,
        )
        return video
    return create
