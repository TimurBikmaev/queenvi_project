from http import HTTPStatus

from django.contrib.auth import get_user_model, login, logout
from django.db.models import Count, Exists, OuterRef, Prefetch, Q
from django.shortcuts import get_object_or_404, redirect
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import (
    AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from api import serializers
from api.mixins import HttpLookupMixin
from core.constants import PublicIdConstants
from post.constants import MediaConstants as MC
from post.errors import UserCanReportError
from post.models import Comment, Like, Media, Post, Report
from post.utils import MediaUtils
from post.validators import can_user_report_post
from user.errors import StateValidationError
from user.permissions import IsOwner
from user.services import TwitchLoginService
from youtube_suggestion.models import Video


User = get_user_model()


class UserViewSet(HttpLookupMixin, mixins.RetrieveModelMixin, GenericViewSet):
    queryset = User.objects.all()
    serializer_class = serializers.UserSerializer
    lookup_field = 'username'
    permission_classes = [AllowAny]

    def get_queryset(self):
        return User.objects.annotate(
            posts_count=Count(
                'posts',
                filter=Q(posts__is_banned=False),
            )
        ).prefetch_related(
            Prefetch(
                'posts',
                queryset=Post.objects.filter(is_banned=False).annotate(
                    likes_count=Count('likes'),
                    comments_count=Count('comments')
                ),
                to_attr='visible_posts',
            )
        )

    @action(detail=False, methods=['get'])
    def twitch_login(self, request):
        return redirect(TwitchLoginService.get_login_url(request))

    @action(detail=False, methods=['get'])
    def twitch_callback(self, request):
        try:
            user = TwitchLoginService.authenticate(request)
        except StateValidationError as e:
            raise ValidationError(e.message)
        login(request, user)
        return redirect('profile-detail', username=user.username)

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def logout(self, request):
        logout(request)
        return redirect('posts-list')

    @action(
        detail=False,
        methods=['patch', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def avatar(self, request):
        user = self.get_queryset().get(pk=request.user.pk)
        if request.method == 'DELETE':
            if not user.custom_avatar:
                return Response(
                    {'detail': 'Аватар не установлен'},
                    status=HTTPStatus.BAD_REQUEST
                )
            user.custom_avatar.delete(save=False)
            user.custom_avatar = None
            user.save()
            serializer = self.get_serializer(user)
            return Response(serializer.data, HTTPStatus.OK)

        serializer = self.get_serializer(
            user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        if 'custom_avatar' in serializer.validated_data and user.custom_avatar:
            user.custom_avatar.delete(save=False)
        serializer.save()
        return Response(serializer.data, HTTPStatus.OK)


class PostViewSet(HttpLookupMixin, ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = serializers.PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwner]

    def get_serializer_class(self):
        if self.action == 'list':
            return serializers.ShortPostSerializer
        elif self.action == 'reports':
            return serializers.CreateReportSerializer
        return serializers.PostSerializer

    def get_queryset(self):
        queryset = Post.objects.annotate(
            likes_count=Count('likes'),
            comments_count=Count('comments'),
        )
        if self.request.user.is_authenticated:
            queryset = queryset.annotate(
                is_liked=Exists(Like.objects.filter(
                    post=OuterRef('pk'),
                    user=self.request.user
                ))
            )
        if self.action == 'list':
            queryset = queryset.prefetch_related(Prefetch(
                'media',
                queryset=Media.objects.filter(order=MC.PREVIEW_ORDER),
                to_attr='preview_media'
            ))
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        post = self.get_object()
        MediaUtils.del_media_catalog(post.public_id)
        self.perform_destroy(post)
        return Response(status=HTTPStatus.NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def like(self, request, public_id=None):
        post = self.get_object()
        if request.method == 'POST':
            Like.objects.get_or_create(post=post, user=request.user)
        else:
            Like.objects.filter(post=post, user=request.user).delete()
        post = self.get_queryset().get(public_id=public_id)
        serializer = self.get_serializer(post)
        return Response(serializer.data, HTTPStatus.OK)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def reports(self, request, public_id=None):
        post = self.get_object()
        try:
            can_user_report_post(request.user, post)
        except UserCanReportError as e:
            raise ValidationError(str(e))
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(post=post, user=request.user)
        return Response(serializer.data, HTTPStatus.CREATED)


class CommentViewSet(
    HttpLookupMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet
):
    queryset = Comment.objects.all()
    serializer_class = serializers.CommentSerializer
    lookup_value_regex = PublicIdConstants.URL_REGEX

    def get_permissions(self):
        if self.action in ('partial_update', 'destroy'):
            return [IsOwner()]
        return [IsAuthenticatedOrReadOnly()]

    def perform_create(self, serializer):
        post = get_object_or_404(Post, public_id=self.kwargs['post_id'])
        serializer.save(user=self.request.user, post=post)


class ReportViewSet(
    HttpLookupMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet
):
    queryset = Report.objects.all()
    serializer_class = serializers.ModerationReportSerializer
    http_method_names = ['get', 'patch']
    # permission_classes = [IsModer]


class VideoViewSet(HttpLookupMixin, ModelViewSet):
    queryset = Video.objects.all()
    serializer_class = serializers.VideoSerializer

    def get_permissions(self):
        if self.action == 'destroy':
            return [IsOwner()]
        return [IsAuthenticatedOrReadOnly()]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
