import logging
from http import HTTPStatus

from django.contrib.auth import get_user_model, logout
from django.db.models import Count, Exists, OuterRef, Prefetch, Q, Value
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular import utils as swg
from rest_framework import mixins, permissions as perm
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.filters import OrderingFilter
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from api import serializers
from api.mixins import HttpLookupMixin, ListUpdateMixin
from core.constants import PublicIdConstants
from core.errors import ChangeObjValidationError
from core.utils import get_queryset_by_filter_is_banned
from post.constants import (
    CommentConstansts,
    MediaConstants as MC,
    MediaType,
    ReportConstants,
)
from post.errors import MediaFormatValidationError, UserCanReportError
from post.filters import PostFilter
from post.models import Comment, Like, Media, Post, Report
from post.utils import MediaUtils
from post.validators import ReportValidator
from user.constants import UserConstants as UC
from user.errors import AuthValidationError, ChangeUserValidationError as CUVE
from user.permissions import NotBannedAllowAny, IsModerOrStreamer, IsOwner
from user.services import TwitchLoginService
from youtube_suggestion import errors as vid_er
from youtube_suggestion.constants import (
    VideoConstants, VideoServiceConstants as VSC
)
from youtube_suggestion.models import Video, Voting


logger = logging.getLogger(__name__)
User = get_user_model()


@swg.extend_schema(tags=['Профиль'])
@swg.extend_schema_view(
    retrieve=swg.extend_schema(
        summary='Получить профиль',
        description=(
            'Возвращает подробную информацию о профиле. '
            'У модератора и стримера отображается статус бана.'
        ),
        responses={
            HTTPStatus.OK: serializers.ProfileSerializer,
            HTTPStatus.NOT_FOUND: swg.OpenApiResponse(
                description=UC.MSG_BAN_404_OBJ
            ),
            HTTPStatus.FORBIDDEN: swg.OpenApiResponse(
                description=UC.MSG_BANNED_USER
            ),
        },
    ),
    partial_update=swg.extend_schema(
        summary='Модерация профиля',
        description=(
            'Изменение статуса бана и роли юзера (изменить роль может '
            'только стример). Доступно только для модератора и стримера.'
        ),
        request=serializers.ModerationProfileSerializer,
        responses={
            HTTPStatus.OK: serializers.ProfileSerializer,
            HTTPStatus.FORBIDDEN: swg.OpenApiResponse(
                description=f'{UC.MSG_ANON_AND_BANNED} | {UC.MSG_ONLY_STAFF}'
            ),
            HTTPStatus.BAD_REQUEST: swg.OpenApiResponse(
                description=(
                    f'{CUVE()} | {CUVE(streamer=True)} | {CUVE(role=True)} | '
                    f'{CUVE(staff=True)}'
                )
            ),
            HTTPStatus.NOT_FOUND: swg.OpenApiResponse(
                description=UC.MSG_404
            ),
        }
    ),
)
class UserViewSet(
    HttpLookupMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet
):
    lookup_field = 'username'

    def get_permissions(self):
        if self.action == 'partial_update':
            return [NotBannedAllowAny(), IsModerOrStreamer()]

        elif self.action in ('avatar', 'logout'):
            return [perm.IsAuthenticated(), NotBannedAllowAny()]

        return [NotBannedAllowAny()]

    def get_serializer_class(self):
        user = self.request.user

        if user.is_authenticated and not user.is_user:
            return serializers.ModerationProfileSerializer

        return serializers.ProfileSerializer

    def get_queryset(self):
        """В профиле юзера обычные юзеры видят только незабаненные посты,
        модераторы и стримеры видят любые посты по параметру."""
        user = self.request.user

        if not user.is_authenticated or user.is_user:
            user_queryset = User.objects.filter(is_banned=False)
        else:
            user_queryset = User.objects.all()

        post_queryset = get_queryset_by_filter_is_banned(
            user, self.request, Post
        )

        is_liked_value = Value(False)
        if user.is_authenticated:
            is_liked_value = Exists(Like.objects.filter(
                post=OuterRef('pk'),
                user=self.request.user
            ))

        return user_queryset.annotate(
            posts_count=Count(
                'posts',
                filter=Q(posts__is_banned=False),
                distinct=True
            )
        ).prefetch_related(
            Prefetch(
                'posts',
                queryset=post_queryset.annotate(
                    likes_count=Count('likes', distinct=True),
                    comments_count=Count('comments', distinct=True),
                    is_liked=is_liked_value
                ).order_by(
                    '-created_at'
                ).prefetch_related(
                    Prefetch(
                        'media',
                        queryset=Media.objects.filter(order=MC.PREVIEW_ORDER),
                        to_attr='preview_media'
                    )
                ),
                to_attr='visible_posts',
            )
        )

    @swg.extend_schema(
        tags=['Аутентификация'],
        summary='Аутентификация через Twitch OAuth',
        description=(
            'Необходимо открыть URL в адресной строке браузера. '
            'Эндпоинт перенаправит пользователя на страницу авторизации '
            'Twitch. После успешной авторизации будет создана '
            'пользовательская сессия. Для выполнения авторизованных запросов '
            'через Postman необходимо получить значения cookies "sessionid" и '
            '"csrftoken" в DevTools и передавать их в заголовках запросов: '
            '"Cookie: sessionid=<...>; csrftoken=<...>" и для '
            'запросов, изменяющих данные: "X-CSRFToken: <...>".'
        ),
        responses={
            HTTPStatus.OK: serializers.ProfileSerializer,
            HTTPStatus.BAD_REQUEST: swg.OpenApiResponse(
                description=AuthValidationError.msg
            ),
        },
    )
    @action(detail=False, methods=['get'])
    def twitch_login(self, request):
        return redirect(TwitchLoginService.get_login_url(request))

    @swg.extend_schema(exclude=True)
    @action(detail=False, methods=['get'])
    def twitch_callback(self, request):
        try:
            user = TwitchLoginService.authenticate(request)
        except AuthValidationError as e:
            raise ValidationError(e.msg)

        return redirect('profile-detail', username=user.username)

    @swg.extend_schema(
        tags=['Аутентификация'],
        summary='Разлогин пользователя',
        description='Удаляет сессию пользователя',
        request=None,
        responses={
            HTTPStatus.OK: None,
            HTTPStatus.FORBIDDEN: swg.OpenApiResponse(
                description=UC.MSG_ANON_AND_BANNED,
            )
        },
    )
    @action(detail=False, methods=['post'])
    def logout(self, request):
        logout(request)
        return redirect('posts-list')

    @swg.extend_schema(
        methods=['PATCH'],
        summary='Изменить аватарку профиля',
        description=(
            'Загружает новую аватарку профиля. Можно загрузить изображение '
            f'с разрешением {UC.AVATAR_MAX_WIDTH}x{UC.AVATAR_MAX_HEIGHT} '
            f'и размером до {UC.AVATAR_MAX_SIZE_MB} МБ. '
            'После установки используется кастомная аватарка.'
        ),
        request=serializers.AvatarProfileSerializer,
        responses={
            HTTPStatus.OK: serializers.ProfileSerializer,
            HTTPStatus.FORBIDDEN: swg.OpenApiResponse(
                description=UC.MSG_ANON_AND_BANNED
            ),
            HTTPStatus.BAD_REQUEST: swg.OpenApiResponse(
                description=f'{UC.MSG_RESOLUTION} | {UC.MSG_SIZE}'
            ),
        }
    )
    @swg.extend_schema(
        methods=['DELETE'],
        summary='Удалить аватарку профиля',
        description=(
            'Удаляет кастомную аватарку профиля. '
            'После удаления снова используется аватарка Twitch.'
        ),
        responses={
            HTTPStatus.OK: serializers.ProfileSerializer,
            HTTPStatus.FORBIDDEN: swg.OpenApiResponse(
                description=UC.MSG_ANON_AND_BANNED
            ),
            HTTPStatus.BAD_REQUEST: swg.OpenApiResponse(
                description='Кастомная аватарка не установлена.'
            ),
        },
    )
    @action(
        detail=False,
        methods=['patch', 'delete'],
        parser_classes=[MultiPartParser],
    )
    def avatar(self, request):
        user = self.get_queryset().get(pk=request.user.pk)

        if request.method == 'DELETE':
            if not user.custom_avatar:
                logger.warning(
                    'Юзер %s (%s) попытался удалить неустановленную авку',
                    user.username,
                    user.role
                )
                return Response(
                    {'detail': 'Аватар не установлен'},
                    status=HTTPStatus.BAD_REQUEST
                )

            user.custom_avatar.delete(save=False)
            user.custom_avatar = None
            user.save()

            logger.info(
                'Юзер %s (%s) удалил авку',
                user.username,
                user.role
            )

            serializer = self.get_serializer(user)
            return Response(serializer.data, HTTPStatus.OK)

        serializer = serializers.AvatarProfileSerializer(
            user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)

        if 'custom_avatar' in serializer.validated_data and user.custom_avatar:
            user.custom_avatar.delete(save=False)

        serializer.save()

        logger.info(
            'Юзер %s (%s) изменил свою авку',
            user.username,
            user.role
        )

        serializer = self.get_serializer(user)
        return Response(serializer.data, HTTPStatus.OK)


@swg.extend_schema(tags=['Посты'])
@swg.extend_schema_view(
    list=swg.extend_schema(
        summary='Получить список публикаций',
        description=(
            'Возвращает список пользовательских публикаций. По умолчанию '
            'возвращаются незабаненные публикации, отфильтрованные для '
            'просмотра на стриме и отсортированные от новых к старым. '
            'Доступна фильтрация по типу медиафайлов, флагу "для стрима", '
            'периоду создания и сортировка по количеству лайков '
            'и комментариев. Модератору и стримеру отображается статус бана, '
            'а также доступна фильтрация по статусу бана.'
        ),
        parameters=[
            swg.OpenApiParameter(
                name='ordering',
                description='Сортировка публикаций',
                required=False,
                type=str,
                enum=['likes_count', 'comments_count'],
            ),
            swg.OpenApiParameter(
                name='is_banned',
                description=(
                    'Фильтрация по статусу бана. По умолчанию false. Для '
                    'отображения забаненных постов установите true.'
                    'Доступна только модератору и стримеру.'
                ),
                required=False,
                type=str,
                enum=['true', 'false', 'all'],
            ),
            swg.OpenApiParameter(
                name='is_for_stream',
                description=(
                    'Фильтрация "для стрима". По умолчанию true. '
                    'Для отображения постов, не предназначенных для стрима, '
                    'передайте false.'
                ),
                required=False,
                type=bool,

            ),
            swg.OpenApiParameter(
                name='media',
                description='Фильтрация по типу медиа у публикаций',
                required=False,
                type=str,
                enum=MediaType.values
            ),
            swg.OpenApiParameter(
                name='created',
                description='Фильтрация по периоду создания публикаций',
                required=False,
                type=str,
                enum=['today', 'week', 'month', 'year']
            )
        ],
        responses={
            HTTPStatus.OK: serializers.ShortPostSerializer,
            HTTPStatus.FORBIDDEN: swg.OpenApiResponse(
                description=UC.MSG_BANNED_USER
            ),
        },
    ),
    retrieve=swg.extend_schema(
        summary='Получить публикацию',
        description=(
            'Подробное отображение поста с полным списком медиа. Для '
            'модератора и стримера доступно изменение статуса бана.'
        ),
        responses={
            HTTPStatus.OK: serializers.PostSerializer,
            HTTPStatus.NOT_FOUND: swg.OpenApiResponse(
                description=UC.MSG_BAN_404_OBJ
            ),
            HTTPStatus.FORBIDDEN: swg.OpenApiResponse(
                description=UC.MSG_BANNED_USER
            ),
        },
    ),
    create=swg.extend_schema(
        summary='Создать публикацию',
        description=(
            'Для создания публикации необходимо написать заголовок '
            'и загрузить медиа.'
        ),
        responses={
            HTTPStatus.OK: serializers.PostSerializer,
            HTTPStatus.BAD_REQUEST: swg.OpenApiResponse(
                description=MediaFormatValidationError.msg
            ),
            HTTPStatus.FORBIDDEN: swg.OpenApiResponse(
                description=UC.MSG_ANON_AND_BANNED
            ),
        },
    ),
    partial_update=swg.extend_schema(
        summary='Обновить публикацию',
        description=(
            'Обновить публикацию. Для модератора и стримера '
            'доступно изменение статуса бана.'
        ),
        responses={
            HTTPStatus.OK: serializers.PostSerializer,
            HTTPStatus.BAD_REQUEST: swg.OpenApiResponse(
                description=MediaFormatValidationError.msg
            ),
            HTTPStatus.FORBIDDEN: swg.OpenApiResponse(
                description=f'{UC.MSG_ANON_AND_BANNED} | {UC.MSG_NOT_AUTHOR}'
            ),
            HTTPStatus.NOT_FOUND: swg.OpenApiResponse(
                description=UC.MSG_BAN_404_OBJ
            ),
        },
    ),
    destroy=swg.extend_schema(
        summary='Удалить публикацию',
        description='Удаление публикации доступно только автору.',
        responses={
            HTTPStatus.NO_CONTENT: None,
            HTTPStatus.FORBIDDEN: swg.OpenApiResponse(
                description=f'{UC.MSG_ANON_AND_BANNED} | {UC.MSG_NOT_AUTHOR}'
            ),
        },
    ),
)
class PostViewSet(HttpLookupMixin, ModelViewSet):
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = PostFilter

    ordering_fields = ['likes_count', 'comments_count']
    ordering = ['-created_at']

    parser_classes = [MultiPartParser, JSONParser]

    def get_permissions(self):
        user = self.request.user

        if user.is_authenticated and not user.is_user:
            if self.action == 'partial_update':
                return [
                    perm.IsAuthenticated(),
                    IsModerOrStreamer(),
                    NotBannedAllowAny(),
                ]

        if self.action in ('like', 'report'):
            return [perm.IsAuthenticated(), NotBannedAllowAny()]

        return [
            NotBannedAllowAny(), perm.IsAuthenticatedOrReadOnly(), IsOwner()
        ]

    def get_serializer_class(self):
        user = self.request.user

        if user.is_authenticated and not user.is_user:
            if self.action == 'list':
                return serializers.ModerationShortPostSerializer

            elif self.action in ('retrieve', 'partial_update'):
                post = self.get_object()
                if post.user != user:
                    return serializers.ModerationPostSerializer

        if self.action == 'list':
            return serializers.ShortPostSerializer

        elif self.action == 'report':
            return serializers.CreateReportSerializer

        return serializers.PostSerializer

    def get_queryset(self):
        user = self.request.user

        queryset = get_queryset_by_filter_is_banned(
            user, self.request, Post, self.action
        )

        is_liked_value = Value(False)
        if user.is_authenticated:
            is_liked_value = Exists(Like.objects.filter(
                post=OuterRef('pk'),
                user=self.request.user
            ))

        queryset = queryset.annotate(
            likes_count=Count('likes', distinct=True),
            comments_count=Count('comments', distinct=True),
            is_liked=is_liked_value
        )

        if self.action == 'list':
            param = self.request.query_params.get('is_for_stream')

            if param is not None:
                param_value = param.lower() == 'true'
                queryset = queryset.filter(is_for_stream=param_value)
            else:
                queryset = queryset.filter(is_for_stream=True)

            queryset = queryset.prefetch_related(Prefetch(
                'media',
                queryset=Media.objects.filter(order=MC.PREVIEW_ORDER),
                to_attr='preview_media'
            ))

        elif self.action == 'retrieve':
            queryset = queryset.prefetch_related(
                Prefetch(
                    'media',
                    queryset=Media.objects.order_by('order'),
                    to_attr='list_media',
                )
            )

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        user = request.user

        post = self.get_object()
        old_public_id = post.public_id

        MediaUtils.del_media_catalog(post.public_id)

        self.perform_destroy(post)

        logger.info(
            'Юзер %s (%s) удалил пост %s',
            user.username,
            user.role,
            old_public_id
        )

        return Response(status=HTTPStatus.NO_CONTENT)

    @swg.extend_schema(tags=['Лайки'])
    @swg.extend_schema(
        methods=['POST'],
        summary='Поставить лайк на публикацию',
        description='Лайки повышают популярность публикации.',
        request=None,
        responses={
            HTTPStatus.OK: serializers.PostSerializer,
            HTTPStatus.FORBIDDEN: swg.OpenApiResponse(
                description=UC.MSG_ANON_AND_BANNED
            ),
            HTTPStatus.NOT_FOUND: swg.OpenApiResponse(
                description=UC.MSG_BAN_404_OBJ
            ),
        }
    )
    @swg.extend_schema(
        methods=['DELETE'],
        summary='Убрать лайк с публикации',
        description='Удаления лайков снижает популярность публикации.',
        request=None,
        responses={
            HTTPStatus.OK: serializers.PostSerializer,
            HTTPStatus.FORBIDDEN: swg.OpenApiResponse(
                description=UC.MSG_ANON_AND_BANNED
            ),
            HTTPStatus.NOT_FOUND: swg.OpenApiResponse(
                description=UC.MSG_BAN_404_OBJ
            ),
        }
    )
    @action(detail=True, methods=['post', 'delete'])
    def like(self, request, public_id=None):
        post = self.get_object()

        if request.method == 'POST':
            Like.objects.get_or_create(post=post, user=request.user)
        else:
            Like.objects.filter(post=post, user=request.user).delete()

        post = self.get_queryset().get(public_id=public_id)

        serializer = self.get_serializer(post)
        return Response(serializer.data, HTTPStatus.OK)

    @swg.extend_schema(
        tags=['Жалобы'],
        summary='Пожаловаться на публикацию',
        description=(
            'Жалоба пользователя позволяет эффективнее модерировать контент.'
        ),
        request=serializers.CreateReportSerializer,
        responses={
            HTTPStatus.OK: swg.OpenApiResponse(
                description=ReportConstants.MSG_CREATED
            ),
            HTTPStatus.BAD_REQUEST: swg.OpenApiResponse(
                description=(
                    f'{ReportConstants.MSG_CANNOT_REPORT_STAFF} | '
                    f'{ReportConstants.MSG_OTHER_WITHOUT_REASON}'
                )
            ),
            HTTPStatus.FORBIDDEN: swg.OpenApiResponse(
                description=UC.MSG_ANON_AND_BANNED
            ),
            HTTPStatus.NOT_FOUND: swg.OpenApiResponse(
                description=UC.MSG_BAN_404_OBJ
            ),
        }
    )
    @action(
        detail=True,
        methods=['post'],
        parser_classes=[JSONParser],
    )
    def report(self, request, public_id=None):
        post = self.get_object()

        try:
            ReportValidator.check_report(request.user, post)
        except UserCanReportError as e:
            raise ValidationError(str(e))

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(post=post, user=request.user)

        return Response(serializer.data, HTTPStatus.CREATED)


@swg.extend_schema(tags=['Комментарии'])
@swg.extend_schema_view(
    list=swg.extend_schema(
        summary='Получить список комментариев',
        description=(
            'Возвращает список комментариев незабаненных пользователей, '
            'отсортированнных от новых к старым, к публикации. '
            'Модератор и стример может фильтровать комментарии '
            'по статусу бана пользователя.'
        ),
        parameters=[
            swg.OpenApiParameter(
                name='is_banned',
                description=(
                    'Фильтрация по статусу бана пользователя. По умолчанию '
                    'false. Для отображения комментариев забаненных '
                    'пользователей установите true. Доступна только '
                    'модератору и стримеру.'
                ),
                required=False,
                type=str,
                enum=['true', 'false', 'all'],
            ),
        ],
        responses={
            HTTPStatus.OK: serializers.CommentSerializer,
            HTTPStatus.FORBIDDEN: swg.OpenApiResponse(
                description=UC.MSG_BANNED_USER
            ),
            HTTPStatus.NOT_FOUND: swg.OpenApiResponse(
                description=UC.MSG_BAN_404_OBJ
            ),
        },
    ),
    create=swg.extend_schema(
        summary='Создать комментарий',
        description='Создать комментарий для публикации.',
        responses={
            HTTPStatus.OK: serializers.CommentSerializer,
            HTTPStatus.BAD_REQUEST: swg.OpenApiResponse(
                description=(
                    f'Длина комментария > {CommentConstansts.TEXT_MAX_LENGTH}'
                )
            ),
            HTTPStatus.FORBIDDEN: swg.OpenApiResponse(
                description=UC.MSG_ANON_AND_BANNED
            ),
            HTTPStatus.NOT_FOUND: swg.OpenApiResponse(
                description=UC.MSG_BAN_404_OBJ
            ),
        },
    ),
    partial_update=swg.extend_schema(
        summary='Обновить комментарий',
        description='Обновление комментария доступно только автору.',
        responses={
            HTTPStatus.OK: serializers.CommentSerializer,
            HTTPStatus.BAD_REQUEST: swg.OpenApiResponse(
                description=(
                    f'Длина комментария > {CommentConstansts.TEXT_MAX_LENGTH}'
                )
            ),
            HTTPStatus.FORBIDDEN: swg.OpenApiResponse(
                description=UC.MSG_ANON_AND_BANNED
            ),
            HTTPStatus.NOT_FOUND: swg.OpenApiResponse(
                description=UC.MSG_BAN_404_OBJ
            ),
        },
    ),
    destroy=swg.extend_schema(
        summary='Удалить комментарий',
        description=(
            'Удаление комментария доступно автору, модератору и стримеру.'
        ),
        responses={
            HTTPStatus.NO_CONTENT: None,
            HTTPStatus.FORBIDDEN: swg.OpenApiResponse(
                description=(
                    f'{UC.MSG_ANON_AND_BANNED} | {UC.MSG_NOT_AUTHOR} | '
                    f'{UC.MSG_ONLY_STAFF}'
                )
            ),
            HTTPStatus.NOT_FOUND: swg.OpenApiResponse(
                description=UC.MSG_BAN_404_OBJ
            ),
        },
    ),
)
class CommentViewSet(
    HttpLookupMixin,
    ListUpdateMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet
):
    serializer_class = serializers.CommentSerializer
    lookup_value_regex = PublicIdConstants.URL_REGEX
    filter_backends: list = []

    def get_permissions(self):
        user = self.request.user

        if (
            (user.is_authenticated and not user.is_user)
            and self.action == 'destroy'
        ):
            return [NotBannedAllowAny(), IsModerOrStreamer()]

        if self.action in ('partial_update', 'destroy'):
            return [NotBannedAllowAny(), IsOwner()]

        return [NotBannedAllowAny(), perm.IsAuthenticatedOrReadOnly()]

    def get_queryset(self):
        user = self.request.user

        if user.is_authenticated and not user.is_user:
            is_banned = self.request.query_params.get('is_banned', '')

            if is_banned.lower() == 'true':
                return Comment.objects.filter(user__is_banned=True)
            elif is_banned.lower() == 'all':
                return Comment.objects.filter()

        return Comment.objects.filter(user__is_banned=False)

    def perform_create(self, serializer):
        post = get_object_or_404(Post, public_id=self.kwargs['post_id'])

        serializer.save(user=self.request.user, post=post)

    def create(self, request, *args, **kwargs):
        user = request.user

        post = get_object_or_404(Post, public_id=self.kwargs['post_id'])

        if post.is_banned:
            logger.info(
                'Юзер %s (%s) попытался прокомментить '
                'забаненный пост %s, is_banned = %s',
                user.username,
                user.role,
                post.public_id,
                post.is_banned
            )
            raise ValidationError('Нельзя комментировать забаненный пост')

        comment = super().create(request, *args, **kwargs)

        logger.info(
            'Юзер %s (%s) создал коммент %s на пост %s',
            user.username,
            user.role,
            comment.data['public_id'],
            post.public_id,
        )

        return comment

    def list(self, request, *args, **kwargs):
        user = self.request.user

        post = get_object_or_404(Post, public_id=self.kwargs['post_id'])

        if (not user.is_authenticated or user.is_user) and post.is_banned:
            logger.warning(
                'Юзер %s (%s) попытался посмотреть '
                'забаненный пост %s, is_banned = %s',
                user.username,
                user.role,
                post.public_id,
                post.is_banned
            )
            raise NotFound('Упс... Пост не найден :(')

        return super().list(request, *args, **kwargs)


@swg.extend_schema(tags=['Жалобы'])
@swg.extend_schema_view(
    list=swg.extend_schema(
        summary='Получить список жалоб',
        description=(
            'Возвращает список нерассмотренных жалоб, отсортированных от '
            'новых к старым. Фильтрация по статусу репорта. '
            'Доступно только для модератора и стримера.'
        ),
        responses={
            HTTPStatus.OK: serializers.ModerationReportSerializer,
            HTTPStatus.FORBIDDEN: swg.OpenApiResponse(
                description=(
                    f'{UC.MSG_ANON_AND_BANNED} | {UC.MSG_ONLY_STAFF}'
                )
            ),
        },
    ),
    partial_update=swg.extend_schema(
        summary='Изменить статус жалобы',
        description=(
            'Изменение статуса жалобы напрямую меняет статус бана публикации.'
        ),
        responses={
            HTTPStatus.OK: serializers.CommentSerializer,
            HTTPStatus.BAD_REQUEST: swg.OpenApiResponse(
                description=(
                    f'{ReportConstants.MSG_STATUS_TO_NOT_VIEWED}'
                )
            ),
            HTTPStatus.FORBIDDEN: swg.OpenApiResponse(
                description=(
                    f'{UC.MSG_ANON_AND_BANNED} | {UC.MSG_ONLY_STAFF}'
                )
            ),
            HTTPStatus.NOT_FOUND: swg.OpenApiResponse(
                description=UC.MSG_404
            ),
        },
    ),
)
class ReportViewSet(
    HttpLookupMixin,
    ListUpdateMixin,
    GenericViewSet
):
    serializer_class = serializers.ModerationReportSerializer

    http_method_names = ['get', 'patch']
    permission_classes = [NotBannedAllowAny, IsModerOrStreamer]

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status']

    def get_queryset(self):
        queryset = Report.objects.all()

        if 'status' not in self.request.query_params:
            queryset = queryset.filter(status='not_viewed')

        return queryset


@swg.extend_schema(tags=['Предложка видео'])
@swg.extend_schema_view(
    list=swg.extend_schema(
        summary='Получить список рекомендованных видео',
        description=(
            'Возвращает список рекомендованных для просмотра на стриме видео '
            'из YouTube. По умолчанию возвращаются незабаненные видео, '
            'отсортированные по убыванию количества голосов. Доступна '
            'фильтрация по категориям и сортировка по дате создания. '
            'Модератору и стримеру отображается статус бана, '
            'а также доступна фильтрация по статусу бана.'
        ),
        parameters=[
            swg.OpenApiParameter(
                name='ordering',
                description='Сортировка видео из предложки',
                required=False,
                type=str,
                enum=['created_at', '-created_at',],
            ),
            swg.OpenApiParameter(
                name='is_banned',
                description=(
                    'Фильтрация по статусу бана. По умолчанию false. Для '
                    'отображения забаненных постов установите true.'
                    'Доступна только модератору и стримеру.'
                ),
                required=False,
                type=str,
                enum=['true', 'false', 'all'],
            )
        ],
        responses={
            HTTPStatus.OK: serializers.VideoSerializer,
            HTTPStatus.FORBIDDEN: swg.OpenApiResponse(
                description=UC.MSG_BANNED_USER
            ),
        },
    ),
    create=swg.extend_schema(
        summary='Предложить видео',
        description=(
            'Предожить видео для просмотра на стриме. Необходимо вставить '
            f'ссылку из Youtube с доменами: "{VSC.URL_VIDEO_YOUTUBE_1}" '
            f'или "{VSC.URL_VIDEO_YOUTUBE_2}" и выбрать категорию.'
        ),
        responses={
            HTTPStatus.OK: serializers.VideoSerializer,
            HTTPStatus.BAD_REQUEST: swg.OpenApiResponse(
                description=(
                    f'{vid_er.VideoAlreadyExistsError()} | '
                    f'{vid_er.VideoAlreadyExistsError(is_banned=True)} | '
                    f'{vid_er.VideoIdIncorrectError()} | '
                    f'{vid_er.VideoRequestError()}.'
                )
            ),
            HTTPStatus.FORBIDDEN: swg.OpenApiResponse(
                description=UC.MSG_ANON_AND_BANNED
            ),
        },
    ),
    partial_update=swg.extend_schema(
        summary='Обновить видео',
        description=(
            'Изменение категории или комментария к видео для обычного '
            'пользователя. Изменение статуса бана для модератора или стримера.'
        ),
        request=serializers.VideoSerializer,
        responses={
            HTTPStatus.OK: serializers.VideoSerializer,
            HTTPStatus.BAD_REQUEST: swg.OpenApiResponse(
                description=(
                    f'{VideoConstants.MSG_CANNOT_CHANGE_BANNED} | '
                    f'{ChangeObjValidationError()} | '
                    f'{ChangeObjValidationError(streamer=True)}'
                )
            ),
            HTTPStatus.FORBIDDEN: swg.OpenApiResponse(
                description=f'{UC.MSG_ANON_AND_BANNED} | {UC.MSG_NOT_AUTHOR}'
            ),
            HTTPStatus.NOT_FOUND: swg.OpenApiResponse(
                description=UC.MSG_BAN_404_OBJ
            ),
        }
    ),
)
class VideoViewSet(
    HttpLookupMixin,
    ListUpdateMixin,
    mixins.CreateModelMixin,
    GenericViewSet
):
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['category']

    ordering_fields = ['created_at']
    ordering = ['-votings_count', '-created_at']

    def get_serializer_class(self):
        user = self.request.user

        if (
            (not user.is_authenticated or user.is_user)
            or self.action == 'create'
        ):
            return serializers.VideoSerializer

        elif self.action == 'partial_update':
            if self.get_object().user == user:
                return serializers.VideoSerializer

        return serializers.ModerationVideoSerializer

    def get_permissions(self):
        user = self.request.user

        if user.is_authenticated and not user.is_user:
            if self.action == 'partial_update':
                return [
                    perm.IsAuthenticated(),
                    IsModerOrStreamer(),
                    NotBannedAllowAny(),
                ]

        if self.action == 'voting':
            return [perm.IsAuthenticated(), NotBannedAllowAny()]

        return [
            NotBannedAllowAny(),
            perm.IsAuthenticatedOrReadOnly(),
            IsOwner()
        ]

    def get_queryset(self):
        user = self.request.user

        queryset = get_queryset_by_filter_is_banned(
            user, self.request, Video, self.action
        )

        is_voted = Value(False)
        if user.is_authenticated:
            is_voted = Exists(Voting.objects.filter(
                video=OuterRef('pk'),
                user=self.request.user
            ))

        return queryset.annotate(
            is_voted=is_voted,
            votings_count=Count('votes')
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @swg.extend_schema(tags=['Голоса'])
    @swg.extend_schema(
        methods=['POST'],
        summary='Проголосовать за видео',
        description=(
                'Проголосовать за видео. Видео, набравшее наибольшее число '
                'голосов, имеет самые высокие шансы быть просмотренным на '
                'стриме.'
        ),
        request=None,
        responses={
            HTTPStatus.OK: serializers.VideoSerializer,
            HTTPStatus.FORBIDDEN: swg.OpenApiResponse(
                description=UC.MSG_ANON_AND_BANNED
            ),
            HTTPStatus.NOT_FOUND: swg.OpenApiResponse(
                description=UC.MSG_BAN_404_OBJ
            ),
        }
    )
    @swg.extend_schema(
        methods=['DELETE'],
        summary='Убрать голос с видео',
        description=(
                'Убрать голос с видео и понизить шансы '
                'быть просмотренным на стриме.'
        ),
        request=None,
        responses={
            HTTPStatus.OK: serializers.VideoSerializer,
            HTTPStatus.FORBIDDEN: swg.OpenApiResponse(
                description=UC.MSG_ANON_AND_BANNED
            ),
            HTTPStatus.NOT_FOUND: swg.OpenApiResponse(
                description=UC.MSG_BAN_404_OBJ
            ),
        }
    )
    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[NotBannedAllowAny, perm.IsAuthenticated]
    )
    def voting(self, request, public_id=None):
        video = self.get_object()

        if request.method == 'POST':
            Voting.objects.get_or_create(video=video, user=request.user)
        else:
            Voting.objects.filter(video=video, user=request.user).delete()

        video = self.get_queryset().get(public_id=public_id)
        serializer = self.get_serializer(video)

        return Response(serializer.data, HTTPStatus.OK)


@swg.extend_schema(
    tags=['Поиск'],
    summary='Найти пользователя или пост',
    description=(
        'Поиск осуществляется по "username" пользователя и "name" поста.'
    ),
    responses={
        HTTPStatus.OK: serializers.SearchSerializer,
        HTTPStatus.FORBIDDEN: swg.OpenApiResponse(
            description=UC.MSG_BANNED_USER
        ),
    },
)
class SearchView(APIView):
    def get(self, request):
        user = request.user

        param_search = request.query_params.get('find', '')

        if user.is_authenticated and user.is_banned:
            logger.warning(
                'Забаненный юзер %s (%s), is_banned = %s '
                'попытался найти \'%s\'',
                user.username,
                user.role,
                user.is_banned,
                param_search
            )
            raise ValidationError('Забаненным доступ запрещен o_o')

        posts = Post.objects.filter(
            name__icontains=param_search
        ).prefetch_related(
            Prefetch(
                'media',
                queryset=Media.objects.filter(order=MC.PREVIEW_ORDER),
                to_attr='preview_media'
            )
        )

        users = User.objects.filter(username__icontains=param_search.lower())

        if not user.is_authenticated or user.is_user:
            posts = posts.filter(is_banned=False)
            users = users.filter(is_banned=False)

        return Response(
            serializers.SearchSerializer(
                {'posts': posts, 'users': users}
            ).data, HTTPStatus.OK,
        )
