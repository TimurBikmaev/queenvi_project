class SerializersConstants:
    POST_BASE_FIELDS = [
        'public_id', 'user', 'name', 'description', 'is_for_stream',
        'likes_count', 'comments_count', 'is_liked', 'created_at',
        'updated_at',
    ]
    POST_MEDIA_MAX_COUNT = 10
    POST_MEDIA_MIN_COUNT = 1
    POST_PROFILE_DESCRIPTION_MAX_LENGTH = 10
    POST_PROFILE_NAME_MAX_LENGTH = 10
    VIDEO_BASE_FIELDS = [
        'public_id', 'youtube_id', 'user', 'title', 'preview_url',
        'channel_name', 'pub_date', 'duration', 'views_count',
        'likes_count', 'comments_count', 'category', 'comment',
        'is_voted', 'votings_count', 'created_at', 'updated_at',
    ]
