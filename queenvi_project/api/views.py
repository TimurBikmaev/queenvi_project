from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import generics, filters, viewsets
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny

from .serializers import UserSerializer

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    # permission_classes = (OwnerOrReadOnly,)
    # pagination_class = LimitOffsetPagination
