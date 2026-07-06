from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import generics, filters, viewsets
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny

from api.serializers import (
    CreateUserSerializer,
    ShortUserSerializer,
    UpdateUserSerializer,
    UserSerializer,
)
from post.models import Post


User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    # permission_classes = (OwnerOrReadOnly,)
    # pagination_class = LimitOffsetPagination

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            if self.request.user.is_moderator or self.request.user.is_streamer:
                return UserSerializer
            return ShortUserSerializer

        if self.action == 'create':
            return CreateUserSerializer

        if self.action in ['update', 'partial_update']:
            return UpdateUserSerializer

        return UserSerializer


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    # permission_classes = (OwnerOrReadOnly,)
    # pagination_class = LimitOffsetPagination
