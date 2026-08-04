from http import HTTPStatus

from django.contrib.auth import get_user_model, login, logout
from django.db.models import Count, Exists, OuterRef, Prefetch, Q
from django.shortcuts import get_object_or_404, redirect
from rest_framework import mixins, permissions as perm
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from api import serializers
from api.mixins import FilterMixin, HttpLookupMixin, ListUpdateMixin
from core.constants import PublicIdConstants
from post.constants import MediaConstants as MC
from post.errors import UserCanReportError
from post.filters import ModerationPostFilter, PostFilter
from post.models import Comment, Like, Media, Post, Report
from post.utils import MediaUtils
from post.validators import ReportValidator
from user.errors import StateValidationError
from user.permissions import IsModerOrStreamer, IsOwner
from user.services import TwitchLoginService
from youtube_suggestion.models import Video, Voting


User = get_user_model()


class UserViewSet(
    HttpLookupMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet
):
    queryset = User.objects.all()
    lookup_field = 'username'

    def get_permissions(self):
        if self.action == 'partial_update':
            return [IsModerOrStreamer()]
        return [perm.AllowAny()]

    def get_serializer_class(self):
        user = self.request.user
        if user.is_authenticated and not user.is_user:
            return serializers.ModerationSteamerProfileSerializer
        return serializers.ProfileSerializer

    def get_queryset(self):
        return User.objects.annotate(
            posts_count=Count(
                'posts',
                filter=Q(posts__is_banned=False),
            )
        ).prefetch_related(
            Prefetch(
                'posts',
                queryset=Post.objects.filter(is_banned=False)
                .annotate(
                    likes_count=Count('likes'),
                    comments_count=Count('comments')
                )
                .prefetch_related(
                    Prefetch(
                        'media',
                        queryset=Media.objects.filter(order=MC.PREVIEW_ORDER),
                        to_attr='preview_media'
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
        try:
            user = TwitchLoginService.authenticate(request)
        except StateValidationError as e:
            raise ValidationError(e.msg)
        login(request, user)
        return redirect('profile-detail', username=user.username)

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[perm.IsAuthenticated]
    )
    def logout(self, request):
        logout(request)
        return redirect('posts-list')

    @action(
        detail=False,
        methods=['patch', 'delete'],
        permission_classes=[perm.IsAuthenticated]
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

        serializer = serializers.AvatarProfileSerializer(
            user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        if 'custom_avatar' in serializer.validated_data and user.custom_avatar:
            user.custom_avatar.delete(save=False)
        serializer.save()
        serializer = self.get_serializer(user)
        return Response(serializer.data, HTTPStatus.OK)


class PostViewSet(HttpLookupMixin, FilterMixin, ModelViewSet):
    queryset = Post.objects.all()
    ordering_fields = ['likes_count', 'comments_count']

    def get_permissions(self):
        user = self.request.user
        if user.is_authenticated and not user.is_user:
            if self.action == 'partial_update':
                return [perm.IsAuthenticated(), IsModerOrStreamer()]
        return [perm.IsAuthenticatedOrReadOnly(), IsOwner()]

    def get_serializer_class(self):
        user = self.request.user
        if user.is_authenticated and not user.is_user:
            if self.action == 'list':
                return serializers.ModerationShortPostSerializer
            elif self.action in ('retrieve', 'partial_update'):
                return serializers.ModerationPostSerializer

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

    def get_filterset_class(self):
        user = self.request.user
        if user.is_authenticated and not user.is_user:
            return ModerationPostFilter
        return PostFilter

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
        permission_classes=[perm.IsAuthenticated]
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
        permission_classes=[perm.IsAuthenticated]
    )
    def reports(self, request, public_id=None):
        post = self.get_object()
        try:
            ReportValidator.check_report(request.user, post)
        except UserCanReportError as e:
            raise ValidationError(str(e))
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(post=post, user=request.user)
        return Response(serializer.data, HTTPStatus.CREATED)


class CommentViewSet(
    HttpLookupMixin,
    ListUpdateMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet
):
    queryset = Comment.objects.all()
    serializer_class = serializers.CommentSerializer
    lookup_value_regex = PublicIdConstants.URL_REGEX

    def get_permissions(self):
        if self.action in ('partial_update', 'destroy'):
            return [IsOwner()]
        return [perm.IsAuthenticatedOrReadOnly()]

    def perform_create(self, serializer):
        post = get_object_or_404(Post, public_id=self.kwargs['post_id'])
        serializer.save(user=self.request.user, post=post)


class ReportViewSet(
    HttpLookupMixin,
    FilterMixin,
    ListUpdateMixin,
    GenericViewSet
):
    queryset = Report.objects.all()
    serializer_class = serializers.ModerationReportSerializer
    http_method_names = ['get', 'patch']
    permission_classes = [IsModerOrStreamer]
    filterset_fields = ['status']
    ordering_fields = ['created_at']


class VideoViewSet(
    HttpLookupMixin,
    FilterMixin,
    ListUpdateMixin,
    mixins.CreateModelMixin,
    GenericViewSet
):
    queryset = Video.objects.all()
    ordering_fields = ['votings_count']

    def get_serializer_class(self):
        user = self.request.user
        if user.is_authenticated and not user.is_user:
            if self.action in ('list', 'partial_update'):
                return serializers.ModerationVideoSerializer
        return serializers.VideoSerializer

    def get_permissions(self):
        if self.action == 'partial_update' and self.request.user.is_user:
            return [perm.IsAuthenticated(), IsOwner()]
        return [perm.IsAuthenticatedOrReadOnly()]

    def get_queryset(self):
        return Video.objects.filter(is_banned=False).annotate(
            is_voted=Exists(
                Voting.objects.filter(
                    video=OuterRef('pk'),
                    user=self.request.user
                )
            ),
            votings_count=Count('votes')
        )

    def get_filterset_fields(self):
        user = self.request.user
        if user.is_authenticated and not user.is_user:
            return ['category', 'is_banned']
        return ['category']

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[perm.IsAuthenticated]
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
