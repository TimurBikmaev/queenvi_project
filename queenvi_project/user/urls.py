from django.urls import include, path

from user.views import auth_twitch, auth_twitch_callback


twitch_urls = [
    path('twitch/', auth_twitch, name='auth_twitch'),
    path('twitch/callback/', auth_twitch_callback, name='auth_twitch_callback'),
]

urlpatterns = [
    path('auth/', include(twitch_urls)),
]
