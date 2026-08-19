import os
from pathlib import Path

from dotenv import load_dotenv

from core.constants import LoggingConstants


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.environ['DJANGO_SECRET_KEY']
DEBUG = os.environ['DEBUG'].lower() in ('true', '1', 't')
ALLOWED_HOSTS = os.environ['ALLOWED_HOSTS'].split(',')

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
TWITCH_CLIENT_ID = os.getenv('TWITCH_CLIENT_ID')
TWITCH_CLIENT_SECRET = os.getenv('TWITCH_CLIENT_SECRET')
TWITCH_REDIRECT_URI = os.environ['TWITCH_REDIRECT_URI']

LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)
LOGGING = {
    'version': LoggingConstants.CONFIG_VERSION,
    'disable_existing_loggers': False,

    'formatters': {
        'log_style': {
            'format': '{asctime} | {levelname} | {name} | {message}',
            'style': '{',
        },
    },

    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'log_style',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_DIR / 'django.log',
            'maxBytes': LoggingConstants.FILE_MAX_SIZE,
            'backupCount': LoggingConstants.BACKUP_COUNT,
            'formatter': 'log_style',
            'encoding': 'utf-8',
        },
    },

    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
}


INSTALLED_APPS = [
    'api.apps.ApiConfig',
    'post.apps.PostConfig',
    'user.apps.UserConfig',
    'youtube_suggestion.apps.YoutubeSuggestionConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'django_filters',
    'drf_spectacular',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'queenvi_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'queenvi_project.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB'),
        'USER': os.getenv('POSTGRES_USER'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD'),
        'HOST': os.getenv('POSTGRES_HOST'),
        'PORT': os.getenv('POSTGRES_PORT'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


LANGUAGE_CODE = 'ru-ru'

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_TZ = True


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'user.User'


MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / "staticfiles"


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'QueenVi',
    'DESCRIPTION': (
        'Площадка для обмена контентом '
        'внутри фан-сообщества стримерши QueenVi.'
    ),
    'TAGS': [
        {
            'name': 'Аутентификация',
            'description': 'Аутентификация пользователя'
        },
        {'name': 'Профиль', 'description': 'Профиль пользователя'},
        {
            'name': 'Предложка видео', 'description': 'Рекомендованные '
            'пользователями Youtube-видео для просмотра на стриме'
        },
        {
            'name': 'Голоса', 'description': 'Голосование за просмотр '
            'видео из предложки'
        },
        {'name': 'Посты', 'description': 'Публикации пользователей'},
        {'name': 'Лайки', 'description': 'Лайки публикаций'},
        {'name': 'Комментарии', 'description': 'Комментарии к публикациям'},
        {'name': 'Жалобы', 'description': 'Жалобы на посты пользователей'},
        {'name': 'Поиск', 'description': 'Поиск пользователей и постов'},
    ],
    'COMPONENT_SPLIT_REQUEST': True,
    'APPEND_COMPONENTS': {
        'securitySchemes': {
            'csrfAuth': {
                'type': 'apiKey',
                'in': 'header',
                'name': 'X-CSRFToken',
            },
        },
    },
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}
