import logging
import re

from django.conf import settings
import requests

from youtube_suggestion.constants import (
    VideoConstants, VideoServiceConstants as VSC
)
from youtube_suggestion.errors import (
    VideoAlreadyExistsError, VideoIdIncorrectError, VideoRequestError
)
from youtube_suggestion.models import Video


logger = logging.getLogger(__name__)


class VideoSerivce:
    """Обработка данных видео из ютуба."""

    @staticmethod
    def video_uploading(url, user, category, comment):
        video_id = VideoSerivce.parse_video_id(user, url)
        VideoSerivce.get_existed_video(user, video_id)
        data = VideoSerivce.get_video_data(user, video_id)
        return VideoSerivce.create_video(
            data, user, video_id, category, comment
        )

    @staticmethod
    def parse_video_id(user, url: str) -> str:
        if url.startswith(VSC.URL_VIDEO_YOUTUBE_1):
            video_id = url[len(VSC.URL_VIDEO_YOUTUBE_1):]
        elif url.startswith(VSC.URL_VIDEO_YOUTUBE_2):
            video_id = url[len(VSC.URL_VIDEO_YOUTUBE_2):]
        else:
            logger.warning(
                'Юзер %s (%s) попытался загрузить видео '
                'с некорректным url: %s',
                user.username,
                user.role,
                url
            )
            raise VideoIdIncorrectError()
        video_id = video_id[:VideoConstants.VIDEO_ID_MAX_LENGTH]
        if len(video_id) != VideoConstants.VIDEO_ID_MAX_LENGTH:
            logger.warning(
                'Юзер %s (%s) попытался загрузить видео с некорректной '
                'длиной youtube_id %s: %s != %s ',
                user.username,
                user.role,
                video_id,
                len(video_id),
                VideoConstants.VIDEO_ID_MAX_LENGTH
            )
            raise VideoIdIncorrectError()
        return video_id

    @staticmethod
    def get_existed_video(user, video_id):
        """Проверка, что видео уже предлагали."""
        video = Video.objects.filter(youtube_id=video_id).first()
        if video is not None:
            logger.warning(
                'Юзер %s (%s) попытался загрузить '
                'уже существующее видео с youtube_id %s',
                user.username,
                user.role,
                video.youtube_id
            )
            raise VideoAlreadyExistsError(video)

    @staticmethod
    def get_video_data(user, video_id):
        """Получает данные о видео из ютуба."""
        try:
            response = requests.get(
                VSC.URL_GET_VIDEO_DATA,
                params={
                    'part': VSC.PART,
                    'id': video_id,
                    'key': settings.GOOGLE_API_KEY,
                },
            )
            response.raise_for_status()
            return response.json()['items'][VSC.IDX_VIDEO_DATA]
        except IndexError:
            logger.warning(
                'Юзер %s (%s) попытался загрузить недоступное видео с '
                'youtube_id: %s',
                user.username,
                user.role,
                video_id
            )
            raise VideoIdIncorrectError()
        except requests.RequestException:
            logger.exception(
                'При попытке юзера %s (%s) загрузить видео с youtube_id: %s,'
                'произошла сетевая ошибка',
                user.username,
                user.role,
                video_id
            )
            raise VideoRequestError()

    @staticmethod
    def create_video(data, user, video_id, category, comment):
        """Создание объекта видео на основе полученных данных."""
        video = Video.objects.create(
            user=user,
            youtube_id=video_id,
            title=data['snippet']['title'],
            preview_url=VideoSerivce.parse_preview(
                data['snippet']['thumbnails']
            ),
            channel_name=data['snippet']['channelTitle'],
            pub_date=data['snippet']['publishedAt'],
            duration=VideoSerivce.duration_to_sec(
                data['contentDetails']['duration']
            ),
            views_count=data['statistics']['viewCount'],
            likes_count=data['statistics']['likeCount'],
            comments_count=data['statistics']['commentCount'],
            category=category,
            comment=comment
        )
        logger.info(
            'Юзер %s (%s) создал видео %s',
            user.username,
            user.role,
            video.public_id
        )
        return video

    @staticmethod
    def parse_preview(previews):
        """Парсинг превью с самым высоким разрешением"""
        for resolution in VSC.RESOLUTIONS:
            preview = previews.get(resolution)
            if preview is not None:
                preview = preview.get('url')
                break
        return preview

    @staticmethod
    def duration_to_sec(duration):
        """Форматирование даты публикации видео в секунды."""
        match = re.fullmatch(VSC.FORMAT_DURATION, duration)
        hours, minutes, seconds = (
            int(value or VSC.NO_TIME)
            for value in match.groups()
        )
        return (
            hours * VSC.SEC_FROM_HOURS + minutes * VSC.SEC_FROM_MINUTS
            + seconds
        )
