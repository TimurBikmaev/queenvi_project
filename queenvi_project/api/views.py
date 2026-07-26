from http import HTTPStatus

from django.contrib.auth import get_user_model, login, logout
from django.db.models import Count, Exists, OuterRef, Prefetch, Q
from django.shortcuts import get_object_or_404, redirect
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from api import serializers
from api.mixins import HttpLookupMixin
from core.constants import BaseStatus, PublicIdConstants
from core.permissions import IsOwner
from core.services import TwitchLoginService
from post.constants import MediaConstants as MC
from post.models import Comment, Like, Media, Post, Report
from post.utils import MediaUtils
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
                filter=Q(posts__status=BaseStatus.VISIBLE),
            )
        ).prefetch_related(
            Prefetch(
                'posts',
                queryset=Post.objects.filter(
                    status=BaseStatus.VISIBLE
                ).annotate(
                    likes_count=Count('likes'),
                    comments_count=Count(
                        'comments',
                        filter=Q(comments__status=BaseStatus.VISIBLE)
                    )
                ),
                to_attr='visible_posts',
            )
        )

    @action(detail=False, methods=['get'])
    def twitch_login(self, request):
        return redirect(TwitchLoginService.get_login_url(request))

    @action(detail=False, methods=['get'])
    def twitch_callback(self, request):
        user = TwitchLoginService.authenticate(request)
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
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_permissions(self):
        if self.action in ('partial_update', 'destroy'):
            return [IsOwner()]
        return [IsAuthenticatedOrReadOnly()]

    def perform_create(self, serializer):
        post = get_object_or_404(Post, public_id=self.kwargs['post_id'])
        serializer.save(user=self.request.user, post=post)


class ReportViewSet(ModelViewSet):
    queryset = Report.objects.all()
    serializer_class = serializers.ReportSerializer
    http_method_names = ['get', 'post', 'patch']
    lookup_field = 'public_id'


class VideoViewSet(HttpLookupMixin, ModelViewSet):
    queryset = Video.objects.all()
    serializer_class = serializers.VideoSerializer
