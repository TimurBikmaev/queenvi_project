from unittest.mock import patch

from django.utils import timezone
import pytest

from user.constants import UserRole
from youtube_suggestion.constants import Category
from youtube_suggestion.models import Video
from youtube_suggestion.tests.constants import TestVideoConstants as TVC


@pytest.fixture
def mock_youtube_data():
    return {
        'snippet': {
            'title': 'Test video',
            'thumbnails': {
                'maxres': {
                    'url': 'https://example.com/preview.jpg',
                },
            },
            'channelTitle': 'Test channel',
            'publishedAt': '2024-01-01T00:00:00Z',
        },
        'contentDetails': {
            'duration': 'PT1M30S',
        },
        'statistics': {
            'viewCount': '100',
            'likeCount': '10',
            'commentCount': '5',
        },
    }


@pytest.fixture
def mock_youtube_service(mock_youtube_data):
    with patch(
        'youtube_suggestion.services.VideoSerivce.get_video_data',
        return_value=mock_youtube_data,
    ) as mock:
        yield mock


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
