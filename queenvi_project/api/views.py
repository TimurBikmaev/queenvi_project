from django.contrib.auth import get_user_model, login, logout
from django.db.models import Count, Prefetch, Q
from django.shortcuts import redirect
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from api import serializers
from api.mixins import HttpLookupMixin
from core.constants import BaseStatus, PublicIdConstants
from core.services import TwitchLoginService
from post.models import Comment, Like, Media, Post, Report
from youtube_suggestion.models import Video


User = get_user_model()


class UserViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet,
):
    queryset = User.objects.all()
    serializer_class = serializers.UserSerializer
    http_method_names = ['get', 'patch']
    lookup_field = 'username'

    def get_serializer_class(self):
        return super().get_serializer_class()

    def get_profile_queryset(self):
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

    @action(detail=False, methods=['get', 'patch'])
    def me(self, request):
        user = self.get_profile_queryset().get(pk=request.user.pk)
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def twitch_login(self, request):
        return redirect(TwitchLoginService.get_login_url(request))

    @action(detail=False, methods=['get'])
    def twitch_callback(self, request):
        user = TwitchLoginService.authenticate(request)
        login(request, user)
        return redirect('profile-me')


class LogoutAPIView(APIView):

    def post(self, request):
        logout(request)
        return redirect('posts-list')


class PostViewSet(HttpLookupMixin, ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = serializers.PostSerializer

    @action(detail=True, methods=['post', 'delete'])
    def like(self, request):
        ...


class CommentViewSet(
    HttpLookupMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet
):
    queryset = Comment.objects.all()
    serializer_class = serializers.PostSerializer
    lookup_value_regex = PublicIdConstants.URL_REGEX


class ReportViewSet(ModelViewSet):
    queryset = Report.objects.all()
    serializer_class = serializers.ReportSerializer
    http_method_names = ['get', 'post', 'patch']
    lookup_field = 'public_id'


class VideoViewSet(HttpLookupMixin, ModelViewSet):
    queryset = Video.objects.all()
    serializer_class = serializers.VideoSerializer
