from http import HTTPStatus
import secrets
from urllib.parse import urlencode


from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.db.models import Count, Prefetch, Q
from django.shortcuts import redirect
import requests
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api import serializers
from api.constants import TwitchLoginConstants
from api.utils import date_to_json
from core.constants import BaseStatus
from post.models import Post


User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = serializers.UserSerializer
    # permission_classes = (OwnerOrReadOnly,)
    # pagination_class = LimitOffsetPagination

    def get_serializer_class(self):
        if self.action == "me":
            return serializers.ProfileSerializer
        return super().get_serializer_class()

    @action(detail=False, methods=['get'])
    def me(self, request):
        user = User.objects.annotate(posts_count=Count(
            'posts',
            filter=Q(posts__status=BaseStatus.VISIBLE),
        )).prefetch_related(Prefetch(
            'posts',
            queryset=Post.objects.filter(status=BaseStatus.VISIBLE),
            to_attr='visible_posts',
        )).get(pk=request.user.pk)
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def twitch_login(self, request):
        state = secrets.token_urlsafe(TwitchLoginConstants.LENGTH_STATE)
        request.session['oauth_state'] = state
        params = {
            'client_id': settings.TWITCH_CLIENT_ID,
            'redirect_uri': settings.TWITCH_REDIRECT_URI,
            'response_type': TwitchLoginConstants.TYPE_RESPONSE,
            'scope': TwitchLoginConstants.SCOPE,
            'state': state
        }
        return redirect(TwitchLoginConstants.URL_AUTH + urlencode(params))

    @action(detail=False, methods=['get'])
    def twitch_callback(self, request):
        received_state = request.GET.get('state')
        saved_state = request.session.get('oauth_state')
        if received_state != saved_state:
            return Response(
                {'error': 'Регистрация не пройдена!'},
                status=HTTPStatus.BAD_REQUEST
            )

        auth_code = request.GET.get('code')
        response = requests.post(
            TwitchLoginConstants.URL_TOKEN,
            data={
                'client_id': settings.TWITCH_CLIENT_ID,
                'client_secret': settings.TWITCH_CLIENT_SECRET,
                'code': auth_code,
                'grant_type': TwitchLoginConstants.TYPE_GRAND,
                'redirect_uri': settings.TWITCH_REDIRECT_URI,
            },
            timeout=TwitchLoginConstants.TIME_FOR_ANSWER,
        )
        response.raise_for_status()

        data = response.json()
        access_token = f'Bearer {data.get("access_token")}'
        response = requests.get(
            TwitchLoginConstants.URL_USER_INFO,
            headers={
                'Authorization': access_token,
                'Client-Id': settings.TWITCH_CLIENT_ID,
            },
            timeout=TwitchLoginConstants.TIME_FOR_ANSWER,
        )
        response.raise_for_status()
        data = response.json()['data'][TwitchLoginConstants.IDX_USER_DATA]

        user, created = User.objects.get_or_create(
            twitch_id=data["id"],
            defaults={
                "username": data["display_name"],
                "avatar": data["profile_image_url"],
            },
        )
        if not created:
            user.username = data["display_name"]
            user.avatar = data["profile_image_url"]
            user.save(update_fields=["username", "avatar"])

        return redirect('users-me')


# class PostViewSet(viewsets.ModelViewSet):
#     queryset = Post.objects.all()
#     serializer_class = serializers.PostSerializer
#     # permission_classes = (OwnerOrReadOnly,)
#     # pagination_class = LimitOffsetPagination
