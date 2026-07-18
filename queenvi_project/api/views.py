from django.contrib.auth import get_user_model, login
from django.db.models import Count, Prefetch, Q
from django.shortcuts import redirect
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api import serializers
from core.constants import BaseStatus
from core.services import TwitchLoginService
from post.models import Post


User = get_user_model()


class UserViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = User.objects.all()
    serializer_class = serializers.UserSerializer
    http_method_names = ["get", "patch"]

    def get_serializer_class(self):
        if self.action == "me":
            return serializers.ProfileSerializer
        return super().get_serializer_class()

    @action(detail=False, methods=['get'])
    def me(self, request):
        user = User.objects.annotate(
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
        ).get(pk=request.user.pk)
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def twitch_login(self, request):
        return redirect(TwitchLoginService.get_login_url(request))

    @action(detail=False, methods=['get'])
    def twitch_callback(self, request):
        user = TwitchLoginService.authenticate(request)
        login(request, user)
        return redirect('users-me')


# class PostViewSet(viewsets.ModelViewSet):
#     queryset = Post.objects.all()
#     serializer_class = serializers.PostSerializer
#     # permission_classes = (OwnerOrReadOnly,)
#     # pagination_class = LimitOffsetPagination
